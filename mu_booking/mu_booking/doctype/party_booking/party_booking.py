# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cint, cstr, flt, getdate, today

# Booking lifecycle statuses
STATUS_DRAFT = "Draft"
STATUS_CONFIRMED = "Confirmed"
STATUS_SCHEDULED = "Delivery/Installation Scheduled"
STATUS_EXECUTED = "Executed"
STATUS_PENDING_RETURN = "Pending Return"
STATUS_CLOSED = "Closed"
STATUS_CANCELLED = "Cancelled"

ROLE_ADMIN = "System Manager"
ROLE_OFFICER = "Party Booking Officer"
ROLE_INSTALLER = "Party Installation Manager"
ROLE_ACCOUNTANT = "Party Accountant"

WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

# Actions available after confirmation, triggered by form buttons.
# Each action moves the booking from `from` to `to` and is restricted to `roles`
# (System Manager is always allowed). Labels are translated when served.
BOOKING_ACTIONS = {
    "schedule": {
        "label": "Schedule Delivery/Installation",
        "from": STATUS_CONFIRMED,
        "to": STATUS_SCHEDULED,
        "roles": [ROLE_INSTALLER, ROLE_OFFICER],
        "requires_installation_manager": True,
    },
    "execute": {
        "label": "Mark as Executed",
        "from": STATUS_SCHEDULED,
        "to": STATUS_EXECUTED,
        "roles": [ROLE_INSTALLER],
    },
    "await_return": {
        "label": "Wait for Return",
        "from": STATUS_EXECUTED,
        "to": STATUS_PENDING_RETURN,
        "roles": [ROLE_INSTALLER],
    },
}
CONFIRM_ROLES = [ROLE_OFFICER]
CANCEL_ROLES = [ROLE_OFFICER]
CANCELLABLE_STATUSES = (STATUS_CONFIRMED, STATUS_SCHEDULED)
RETURN_ROLES = [ROLE_ACCOUNTANT]


def user_has_role(roles):
    """Return True if the current user has any of `roles` (System Manager always passes)."""
    user_roles = set(frappe.get_roles())
    return ROLE_ADMIN in user_roles or bool(user_roles & set(roles))


def get_weekday_name(date_val):
    """Return translated weekday name for a date value."""
    if not date_val:
        return ""
    d = getdate(date_val)
    return _(WEEKDAY_NAMES[d.weekday()])


def get_nth_weekday_of_month(year, month, week_str, weekday_int):
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    monthcal = c.monthdatescalendar(year, month)
    matching_dates = [d for week in monthcal for d in week if d.month == month and d.weekday() == weekday_int]

    if not matching_dates:
        return None

    if week_str == "1st":
        return matching_dates[0]
    if week_str == "2nd":
        return matching_dates[1] if len(matching_dates) > 1 else None
    if week_str == "3rd":
        return matching_dates[2] if len(matching_dates) > 2 else None
    if week_str == "4th":
        return matching_dates[3] if len(matching_dates) > 3 else None
    if week_str == "Last":
        return matching_dates[-1]
    return None


class PartyBooking(Document):
    def before_validate(self):
        """Auto-create or find Customer based on mobile and name if not provided."""
        if not self.customer and self.customer_name and self.customer_mobile:
            customer_mobile_clean = self.customer_mobile.strip()
            customer_id = frappe.db.get_value("Customer", {"mobile_no": customer_mobile_clean}, "name")
            if not customer_id:
                new_customer = frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": self.customer_name.strip(),
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                    "customer_type": "Individual",
                    "mobile_no": customer_mobile_clean,
                })
                new_customer.insert(ignore_permissions=True)
                customer_id = new_customer.name
            self.customer = customer_id
        elif self.customer and not self.customer_name:
            self.customer_name = frappe.db.get_value("Customer", self.customer, "customer_name")

    def validate(self):
        if self.docstatus == 0:
            self.status = STATUS_DRAFT
        self.set_weekday_fields()
        self.validate_party_date()
        self.validate_recurring()
        self.generate_recurring_sessions()
        self.set_weekday_fields()
        self.sync_asset_quantities_and_values()
        self.check_asset_conflict()

    def before_update_after_submit(self):
        """Allow modifying party_date / party_time on submitted bookings while re-validating conflicts."""
        self.set_weekday_fields()
        self.validate_recurring()
        if self.booking_type == "Recurring" and self.recurring_pattern != "Manual":
            self.generate_recurring_sessions()
            self.set_weekday_fields()
        self.sync_asset_quantities_and_values()
        self.check_asset_conflict()

    def set_weekday_fields(self):
        """Populate party_day and session_day automatically from dates."""
        self.party_day = get_weekday_name(self.party_date)
        for s in self.sessions or []:
            if s.session_date:
                s.session_day = get_weekday_name(s.session_date)

    def sync_asset_quantities_and_values(self):
        """Populate asset_value, total_asset_qty, and available_qty from ERPNext Asset standard fields."""
        target_dates = self.get_booking_dates()
        for d in self.assets or []:
            if not d.asset_name:
                continue
            if cint(d.qty) < 1:
                d.qty = 1
            asset_info = frappe.db.get_value(
                "Asset",
                d.asset_name,
                ["asset_name", "gross_purchase_amount", "asset_quantity"],
                as_dict=True,
            )
            if asset_info:
                if not d.asset_title:
                    d.asset_title = asset_info.asset_name
                if not flt(d.asset_value):
                    d.asset_value = flt(asset_info.gross_purchase_amount)
                total_qty = max(cint(asset_info.asset_quantity), 1)
                d.total_asset_qty = total_qty
                booked_qty = get_max_booked_qty_for_asset(
                    d.asset_name, target_dates, exclude=self.name
                )
                d.available_qty = max(total_qty - booked_qty, 0)

    def get_booking_dates(self):
        """Return the list of dates (as YYYY-MM-DD strings) this booking occupies."""
        if self.booking_type == "Recurring" and self.sessions:
            dates = [
                cstr(getdate(s.session_date))
                for s in self.sessions
                if s.session_date and getattr(s, "session_status", "Scheduled") != "Cancelled"
            ]
            if dates:
                return sorted(set(dates))
        if self.party_date:
            return [cstr(getdate(self.party_date))]
        return []

    def validate_party_date(self):
        """Ensure party date is not in the past for new bookings."""
        if self.is_new() and self.party_date:
            if getdate(self.party_date) < getdate(today()):
                frappe.throw(_("Party Date cannot be in the past."))

    def validate_recurring(self):
        """Validate required fields based on recurring pattern."""
        if self.booking_type == "Recurring":
            if not self.recurring_pattern:
                frappe.throw(_("Please select a Recurring Pattern for a Recurring booking."))

            if self.recurring_pattern == "Manual":
                return

            if not self.start_date:
                frappe.throw(_("Start Date is required for Recurring booking."))

            if self.recurring_pattern == "Daily":
                if not self.number_of_days or int(self.number_of_days) < 1:
                    frappe.throw(_("Number of Days must be at least 1 for Daily recurring booking."))

            elif self.recurring_pattern in ["Weekly", "Monthly"]:
                if not self.end_date:
                    frappe.throw(_("End Date is required for Weekly/Monthly recurring bookings."))
                if getdate(self.end_date) < getdate(self.start_date):
                    frappe.throw(_("End Date cannot be before Start Date."))

    def generate_recurring_sessions(self):
        """Generate sessions dynamically based on the chosen pattern."""
        if self.booking_type != "Recurring":
            self.sessions = []
            return

        if self.recurring_pattern == "Manual":
            return

        if not self.start_date:
            return

        expected_dates = []
        start = getdate(self.start_date)

        if self.recurring_pattern == "Daily":
            for i in range(int(self.number_of_days or 0)):
                expected_dates.append(add_days(start, i))

        elif self.recurring_pattern == "Weekly":
            if not self.end_date:
                return
            end = getdate(self.end_date)

            weekdays = []
            if getattr(self, "monday", 0):
                weekdays.append(0)
            if getattr(self, "tuesday", 0):
                weekdays.append(1)
            if getattr(self, "wednesday", 0):
                weekdays.append(2)
            if getattr(self, "thursday", 0):
                weekdays.append(3)
            if getattr(self, "friday", 0):
                weekdays.append(4)
            if getattr(self, "saturday", 0):
                weekdays.append(5)
            if getattr(self, "sunday", 0):
                weekdays.append(6)

            if not weekdays:
                frappe.throw(_("Please select at least one day of the week."))

            current = start
            while current <= end:
                if current.weekday() in weekdays:
                    expected_dates.append(current)
                current = add_days(current, 1)

        elif self.recurring_pattern == "Monthly":
            if not self.end_date:
                return
            end = getdate(self.end_date)

            if not self.monthly_day or not self.monthly_week:
                frappe.throw(_("Please select Week and Day for Monthly pattern."))

            day_map = {
                "Monday": 0,
                "Tuesday": 1,
                "Wednesday": 2,
                "Thursday": 3,
                "Friday": 4,
                "Saturday": 5,
                "Sunday": 6,
            }
            target_day = day_map[self.monthly_day]

            current_month_start = start.replace(day=1)
            while current_month_start <= end:
                date_to_add = get_nth_weekday_of_month(
                    current_month_start.year,
                    current_month_start.month,
                    self.monthly_week,
                    target_day,
                )
                if date_to_add and start <= date_to_add <= end:
                    expected_dates.append(date_to_add)
                current_month_start = add_months(current_month_start, 1)

        existing_sessions = {cstr(s.session_date): s for s in self.sessions if s.session_date}

        self.sessions = []
        for d in expected_dates:
            d_str = cstr(d)
            if d_str in existing_sessions:
                old_s = existing_sessions[d_str]
                self.append("sessions", {
                    "session_date": d,
                    "session_day": get_weekday_name(d),
                    "session_time": old_s.session_time or self.party_time,
                    "session_status": old_s.session_status,
                    "alternative_asset": old_s.alternative_asset,
                })
            else:
                self.append("sessions", {
                    "session_date": d,
                    "session_day": get_weekday_name(d),
                    "session_time": self.party_time,
                    "session_status": "Scheduled",
                })

    def check_asset_conflict(self):
        """Validate asset availability by date and quantity (using ERPNext Asset.asset_quantity).

        - An asset booked on a future date (e.g. Day 30) remains available on all other dates (e.g. Days 1-29).
        - If an asset has `asset_quantity` > 1 (e.g. 5 tables) and 1 is booked on a date, 4 remain available on that date.
        - If an asset was delivered/executed in a past booking that is still in 'Executed' or 'Pending Return'
          and has not been returned yet, that quantity is held until returned.
        """
        target_dates = self.get_booking_dates()
        if not target_dates:
            return

        # Sum requested quantities per asset in the current booking
        requested_by_asset = {}
        for d in self.assets or []:
            if d.asset_name:
                requested_by_asset[d.asset_name] = requested_by_asset.get(d.asset_name, 0) + max(cint(d.qty), 1)

        # Also check session-specific alternative assets
        alt_requests = []
        for session in self.sessions or []:
            if getattr(session, "alternative_asset", None) and getattr(session, "session_status", "Scheduled") != "Cancelled":
                if session.session_date:
                    alt_requests.append((session.alternative_asset, cstr(getdate(session.session_date))))

        if not requested_by_asset and not alt_requests:
            return

        conflicts = []

        for asset_name, req_qty in requested_by_asset.items():
            total_qty = max(cint(frappe.db.get_value("Asset", asset_name, "asset_quantity")), 1)
            for dt in target_dates:
                booked_qty, holding_bookings = get_booked_qty_and_holders(
                    asset_name, dt, exclude=self.name
                )
                available_qty = max(total_qty - booked_qty, 0)
                if req_qty > available_qty:
                    holders_links = ", ".join(
                        frappe.utils.get_link_to_form("Party Booking", b) for b in holding_bookings
                    )
                    conflicts.append(
                        "<li>"
                        + _(
                            "Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2} "
                            "(Requested: {3}, Available: {4} of {5})"
                        ).format(
                            frappe.utils.escape_html(asset_name),
                            frappe.utils.escape_html(dt),
                            holders_links,
                            req_qty,
                            available_qty,
                            total_qty,
                        )
                        + "</li>"
                    )
                    break

        for alt_asset, dt in alt_requests:
            total_qty = max(cint(frappe.db.get_value("Asset", alt_asset, "asset_quantity")), 1)
            booked_qty, holding_bookings = get_booked_qty_and_holders(
                alt_asset, dt, exclude=self.name
            )
            available_qty = max(total_qty - booked_qty, 0)
            if available_qty < 1:
                holders_links = ", ".join(
                    frappe.utils.get_link_to_form("Party Booking", b) for b in holding_bookings
                )
                conflicts.append(
                    "<li>"
                    + _(
                        "Alternative Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2}"
                    ).format(
                        frappe.utils.escape_html(alt_asset),
                        frappe.utils.escape_html(dt),
                        holders_links,
                    )
                    + "</li>"
                )

        if conflicts:
            items = "".join(conflicts)
            frappe.throw(
                _("The following assets are already booked (conflict detected):")
                + f"<br><br><ul>{items}</ul>",
                title=_("Asset Conflict"),
            )

    def before_submit(self):
        if not user_has_role(CONFIRM_ROLES):
            frappe.throw(_("Only the Booking Officer can confirm a booking."), frappe.PermissionError)
        self.status = STATUS_CONFIRMED

    def on_submit(self):
        self.update_asset_status("Booked")

    def before_cancel(self):
        if not user_has_role(CANCEL_ROLES):
            frappe.throw(_("Only the Booking Officer can cancel a booking."), frappe.PermissionError)
        if self.status not in CANCELLABLE_STATUSES:
            frappe.throw(_("A booking in status {0} cannot be cancelled.").format(_(self.status)))
        self.status = STATUS_CANCELLED

    def on_cancel(self):
        """Revert asset status to Available, but only if it was Booked (not Damaged)."""
        self.update_asset_status_on_cancel()

    def set_status(self, status, **extra_values):
        """Persist a new lifecycle status on a submitted booking and log it in the timeline."""
        self.db_set({"status": status, **extra_values}, notify=True)
        self.add_comment("Info", _("Status changed to {0}").format(_(status)))

    def update_asset_status(self, status):
        """Set all booking assets to the given status."""
        for d in self.assets:
            if d.asset_name:
                frappe.db.set_value("Asset", d.asset_name, "party_booking_status", status)
                d.db_set("asset_booking_status", status)

        if self.booking_type == "Recurring":
            for s in self.sessions:
                if getattr(s, "alternative_asset", None):
                    frappe.db.set_value("Asset", s.alternative_asset, "party_booking_status", status)

    def update_asset_status_on_cancel(self):
        """On cancellation, revert only assets that are still 'Booked' (not Damaged) and have no other active bookings."""
        used_assets = [d.asset_name for d in self.assets if d.asset_name]

        if self.booking_type == "Recurring":
            for s in self.sessions:
                if getattr(s, "alternative_asset", None):
                    used_assets.append(s.alternative_asset)

        for asset_name in set(used_assets):
            current_status = frappe.db.get_value("Asset", asset_name, "party_booking_status")
            if current_status == "Booked":
                other_active = get_active_bookings_holding([asset_name], exclude=self.name)
                if not other_active.get(asset_name):
                    frappe.db.set_value("Asset", asset_name, "party_booking_status", "Available")

        for d in self.assets:
            if d.asset_name:
                if frappe.db.get_value("Asset", d.asset_name, "party_booking_status") == "Available":
                    d.db_set("asset_booking_status", "Available")


def get_booked_qty_and_holders(asset_name, target_date, exclude=None):
    """Return (booked_qty, [booking_names]) for `asset_name` on `target_date`.

    Includes:
    1. Submitted active One-time bookings on `target_date`.
    2. Submitted active Recurring bookings with a non-cancelled session on `target_date`.
    3. Submitted bookings in ('Executed', 'Pending Return') whose party_date < target_date
       and < today() (meaning the asset is physically still out with a past customer).
    """
    if not asset_name or not target_date:
        return 0, []

    target_date_str = cstr(getdate(target_date))
    today_str = cstr(getdate(today()))
    params = {
        "closed": STATUS_CLOSED,
        "cancelled": STATUS_CANCELLED,
        "executed": STATUS_EXECUTED,
        "pending_return": STATUS_PENDING_RETURN,
        "name": exclude or "NEW",
        "asset": asset_name,
        "target_date": target_date_str,
        "today": today_str,
    }

    # 1. Main assets in One-time bookings on the same date, OR overdue unreturned bookings
    main_rows = frappe.db.sql(
        """
        SELECT pb.name, IFNULL(pba.qty, 1) AS qty
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pba.asset_name = %(asset)s
          AND (
              (IFNULL(pb.booking_type, 'One-time') != 'Recurring' AND pb.party_date = %(target_date)s)
              OR (pb.status IN (%(executed)s, %(pending_return)s) AND pb.party_date < %(today)s AND %(target_date)s <= %(today)s)
          )
        """,
        params,
        as_dict=True,
    )

    # 2. Recurring bookings where a session on target_date uses the main assets (no alternative_asset)
    recurring_main_rows = frappe.db.sql(
        """
        SELECT pb.name, IFNULL(pba.qty, 1) AS qty
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
        JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pb.booking_type = 'Recurring'
          AND pba.asset_name = %(asset)s
          AND pbs.session_date = %(target_date)s
          AND IFNULL(pbs.session_status, 'Scheduled') != 'Cancelled'
          AND IFNULL(pbs.alternative_asset, '') = ''
        """,
        params,
        as_dict=True,
    )

    # 3. Recurring bookings where a session on target_date uses this asset as alternative_asset
    alt_rows = frappe.db.sql(
        """
        SELECT pb.name, 1 AS qty
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pbs.alternative_asset = %(asset)s
          AND pbs.session_date = %(target_date)s
          AND IFNULL(pbs.session_status, 'Scheduled') != 'Cancelled'
        """,
        params,
        as_dict=True,
    )

    booked_qty = 0
    holders = []
    for row in main_rows + recurring_main_rows + alt_rows:
        booked_qty += max(cint(row.qty), 1)
        if row.name not in holders:
            holders.append(row.name)

    return booked_qty, holders


def get_max_booked_qty_for_asset(asset_name, target_dates, exclude=None):
    """Return the maximum booked quantity for `asset_name` across `target_dates`."""
    if not asset_name or not target_dates:
        return 0
    return max(
        (get_booked_qty_and_holders(asset_name, dt, exclude=exclude)[0] for dt in target_dates),
        default=0,
    )


def get_active_bookings_holding(assets, exclude=None, target_date=None):
    """Return {asset: booking_name} for assets held by an active submitted booking.

    If `target_date` is provided, only returns bookings that conflict on `target_date`
    and where booked_qty >= asset_quantity.
    """
    assets = list(assets)
    if not assets:
        return {}

    if target_date:
        blocking = {}
        for asset in assets:
            total_qty = max(cint(frappe.db.get_value("Asset", asset, "asset_quantity")), 1)
            booked_qty, holders = get_booked_qty_and_holders(asset, target_date, exclude=exclude)
            if booked_qty >= total_qty and holders:
                blocking[asset] = holders[0]
        return blocking

    params = {
        "closed": STATUS_CLOSED,
        "cancelled": STATUS_CANCELLED,
        "name": exclude or "NEW",
        "assets": tuple(assets),
    }
    main_conflicts = frappe.db.sql(
        """
        SELECT pb.name, pba.asset_name AS asset
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pba.asset_name IN %(assets)s
        """,
        params,
        as_dict=True,
    )
    alt_conflicts = frappe.db.sql(
        """
        SELECT pb.name, pbs.alternative_asset AS asset
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pbs.alternative_asset IN %(assets)s
        """,
        params,
        as_dict=True,
    )

    blocking = {}
    for row in main_conflicts + alt_conflicts:
        blocking.setdefault(row.asset, row.name)
    return blocking


@frappe.whitelist()
def get_asset_availability_info(asset, party_date=None, exclude_booking=None):
    """Return quantity, value, and date-specific availability info for an asset."""
    if not asset:
        return {}

    asset_doc = frappe.db.get_value(
        "Asset",
        asset,
        ["name", "asset_name", "gross_purchase_amount", "asset_quantity", "party_booking_status"],
        as_dict=True,
    )
    if not asset_doc:
        return {}

    total_qty = max(cint(asset_doc.asset_quantity), 1)
    booked_qty = 0
    holding_bookings = []
    if party_date:
        booked_qty, holding_bookings = get_booked_qty_and_holders(
            asset, party_date, exclude=exclude_booking
        )

    available_qty = max(total_qty - booked_qty, 0)

    # Also fetch upcoming active bookings on other dates so the employee can see future schedule clearly
    upcoming = frappe.db.sql(
        """
        SELECT DISTINCT pb.name, pb.party_date, IFNULL(pba.qty, 1) AS qty, pb.status
        FROM `tabParty Booking` pb
        JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
        WHERE pb.docstatus = 1
          AND pb.status NOT IN (%(closed)s, %(cancelled)s)
          AND pb.name != %(name)s
          AND pba.asset_name = %(asset)s
        ORDER BY pb.party_date ASC
        LIMIT 5
        """,
        {
            "closed": STATUS_CLOSED,
            "cancelled": STATUS_CANCELLED,
            "name": exclude_booking or "NEW",
            "asset": asset,
        },
        as_dict=True,
    )

    return {
        "asset": asset_doc.name,
        "asset_title": asset_doc.asset_name,
        "asset_value": flt(asset_doc.gross_purchase_amount),
        "total_asset_qty": total_qty,
        "booked_qty": booked_qty,
        "available_qty": available_qty,
        "holding_bookings": holding_bookings,
        "holding_booking": holding_bookings[0] if (available_qty == 0 and holding_bookings) else None,
        "upcoming_bookings": [
            {
                "name": r.name,
                "party_date": cstr(r.party_date),
                "qty": cint(r.qty),
                "status": r.status,
            }
            for r in upcoming
        ],
    }


@frappe.whitelist()
def get_asset_holding_booking(asset, exclude_booking=None, party_date=None):
    """Return the active booking holding this asset on `party_date` if no quantity remains available."""
    if party_date:
        info = get_asset_availability_info(asset, party_date=party_date, exclude_booking=exclude_booking)
        return info.get("holding_booking")
    return get_active_bookings_holding([asset], exclude=exclude_booking).get(asset)


@frappe.whitelist()
def get_allowed_actions(name):
    """Return the lifecycle buttons the current user may use on this booking."""
    doc = frappe.get_doc("Party Booking", name)
    doc.check_permission("read")

    actions = [
        {
            "action": key,
            "label": _(cfg["label"]),
            "requires_installation_manager": bool(cfg.get("requires_installation_manager")),
        }
        for key, cfg in BOOKING_ACTIONS.items()
        if doc.docstatus == 1 and doc.status == cfg["from"] and user_has_role(cfg["roles"])
    ]
    has_open_return = frappe.db.exists(
        "Party Asset Return", {"party_booking": name, "docstatus": ["<", 2]}
    )
    return {
        "actions": actions,
        "can_confirm": doc.docstatus == 0 and user_has_role(CONFIRM_ROLES),
        "can_cancel": doc.docstatus == 1
        and doc.status in CANCELLABLE_STATUSES
        and user_has_role(CANCEL_ROLES),
        "can_create_return": doc.docstatus == 1
        and doc.status == STATUS_PENDING_RETURN
        and user_has_role(RETURN_ROLES)
        and not has_open_return,
    }


@frappe.whitelist()
def apply_action(name, action, installation_manager=None):
    """Move a submitted booking to the next status after validating role and current status."""
    cfg = BOOKING_ACTIONS.get(action)
    if not cfg:
        frappe.throw(_("Unknown action: {0}").format(action))

    doc = frappe.get_doc("Party Booking", name)
    doc.check_permission("write")

    if doc.docstatus != 1 or doc.status != cfg["from"]:
        frappe.throw(
            _("This action is not allowed while the booking is in status {0}.").format(_(doc.status))
        )
    if not user_has_role(cfg["roles"]):
        frappe.throw(_("You are not allowed to perform this action."), frappe.PermissionError)

    extra_values = {}
    if cfg.get("requires_installation_manager"):
        if not installation_manager:
            frappe.throw(_("Please select the Installation Manager."))
        extra_values["installation_manager"] = installation_manager

    doc.set_status(cfg["to"], **extra_values)
    return doc.status
