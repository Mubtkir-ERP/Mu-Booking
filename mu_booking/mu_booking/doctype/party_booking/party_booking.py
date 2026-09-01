# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, add_months, cstr, getdate, today

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

# Actions available after confirmation, triggered by form buttons.
# Each action moves the booking from `from` to `to` and is restricted to `roles`
# (System Manager is always allowed). Labels are translated when served.
BOOKING_ACTIONS = {
    "schedule": {
        "label": "Schedule Delivery/Installation",
        "from": STATUS_CONFIRMED,
        "to": STATUS_SCHEDULED,
        "roles": [ROLE_INSTALLER],
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


def get_nth_weekday_of_month(year, month, week_str, weekday_int):
    c = calendar.Calendar(firstweekday=calendar.MONDAY)
    monthcal = c.monthdatescalendar(year, month)
    matching_dates = [d for week in monthcal for d in week if d.month == month and d.weekday() == weekday_int]
    
    if not matching_dates:
        return None
        
    if week_str == "1st": return matching_dates[0]
    if week_str == "2nd": return matching_dates[1] if len(matching_dates) > 1 else None
    if week_str == "3rd": return matching_dates[2] if len(matching_dates) > 2 else None
    if week_str == "4th": return matching_dates[3] if len(matching_dates) > 3 else None
    if week_str == "Last": return matching_dates[-1]
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
                    "mobile_no": customer_mobile_clean
                })
                new_customer.insert(ignore_permissions=True)
                customer_id = new_customer.name
            self.customer = customer_id

    def validate(self):
        if self.docstatus == 0:
            self.status = STATUS_DRAFT
        self.validate_party_date()
        self.validate_recurring()
        self.generate_recurring_sessions()
        self.check_asset_conflict()

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
            if not self.end_date: return
            end = getdate(self.end_date)
            
            weekdays = []
            if getattr(self, "monday", 0): weekdays.append(0)
            if getattr(self, "tuesday", 0): weekdays.append(1)
            if getattr(self, "wednesday", 0): weekdays.append(2)
            if getattr(self, "thursday", 0): weekdays.append(3)
            if getattr(self, "friday", 0): weekdays.append(4)
            if getattr(self, "saturday", 0): weekdays.append(5)
            if getattr(self, "sunday", 0): weekdays.append(6)
            
            if not weekdays:
                frappe.throw(_("Please select at least one day of the week."))
                
            current = start
            while current <= end:
                if current.weekday() in weekdays:
                    expected_dates.append(current)
                current = add_days(current, 1)

        elif self.recurring_pattern == "Monthly":
            if not self.end_date: return
            end = getdate(self.end_date)
            
            if not self.monthly_day or not self.monthly_week:
                frappe.throw(_("Please select Week and Day for Monthly pattern."))
                
            day_map = {"Monday":0, "Tuesday":1, "Wednesday":2, "Thursday":3, "Friday":4, "Saturday":5, "Sunday":6}
            target_day = day_map[self.monthly_day]
            
            current_month_start = start.replace(day=1)
            while current_month_start <= end:
                date_to_add = get_nth_weekday_of_month(current_month_start.year, current_month_start.month, self.monthly_week, target_day)
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
                    "session_time": old_s.session_time or self.party_time,
                    "session_status": old_s.session_status,
                    "alternative_asset": old_s.alternative_asset
                })
            else:
                self.append("sessions", {
                    "session_date": d,
                    "session_time": self.party_time,
                    "session_status": "Scheduled"
                })

    def check_asset_conflict(self):
        """Block booking any asset that belongs to an active (not yet returned) booking.

        Per the business rules, an asset does not become available when a party
        date passes -- only when its Asset Return document is submitted and the
        booking is closed (or the booking is cancelled). So one active submitted
        booking locks the asset for any other date.
        """
        requested_assets = {d.asset_name for d in self.assets if d.asset_name}
        for session in self.sessions or []:
            if getattr(session, "alternative_asset", None):
                requested_assets.add(session.alternative_asset)

        if not requested_assets:
            return

        # Assets picked in the assets table of an active booking
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
            {
                "closed": STATUS_CLOSED,
                "cancelled": STATUS_CANCELLED,
                "name": self.name or "NEW",
                "assets": tuple(requested_assets),
            },
            as_dict=True,
        )

        # Assets picked as per-session alternatives in an active booking
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
            {
                "closed": STATUS_CLOSED,
                "cancelled": STATUS_CANCELLED,
                "name": self.name or "NEW",
                "assets": tuple(requested_assets),
            },
            as_dict=True,
        )

        blocking_booking_by_asset = {}
        for row in main_conflicts + alt_conflicts:
            blocking_booking_by_asset.setdefault(row.asset, row.name)

        if not blocking_booking_by_asset:
            return

        items = "".join(
            "<li>"
            + _("Asset <b>{0}</b> is held by active Booking {1} and has not been returned yet").format(
                asset, frappe.utils.get_link_to_form("Party Booking", booking)
            )
            + "</li>"
            for asset, booking in sorted(blocking_booking_by_asset.items())
        )
        frappe.throw(
            _("The following assets are not available:")
            + f"<br><br><ul>{items}</ul><br>"
            + _("An asset becomes available only after its Asset Return document is submitted."),
            title=_("Asset Not Available"),
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
        """On cancellation, revert only assets that are still 'Booked' (not Damaged)."""
        used_assets = [d.asset_name for d in self.assets if d.asset_name]
        
        if self.booking_type == "Recurring":
            for s in self.sessions:
                if getattr(s, "alternative_asset", None):
                    used_assets.append(s.alternative_asset)
                    
        for asset_name in set(used_assets):
            current_status = frappe.db.get_value("Asset", asset_name, "party_booking_status")
            if current_status == "Booked":
                frappe.db.set_value("Asset", asset_name, "party_booking_status", "Available")
                
        # Also update child table rows for main assets
        for d in self.assets:
            if d.asset_name:
                if frappe.db.get_value("Asset", d.asset_name, "party_booking_status") == "Available":
                    d.db_set("asset_booking_status", "Available")


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
