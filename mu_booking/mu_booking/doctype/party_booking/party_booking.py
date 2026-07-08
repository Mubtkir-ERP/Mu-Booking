# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, add_months, getdate, today, cstr
from frappe import _
import calendar

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

    def get_booking_dates(self):
        """Return list of unique dates covered by this booking."""
        dates = []
        if self.booking_type == "One-time":
            if self.party_date:
                dates.append(str(self.party_date))
        else:
            for s in self.sessions:
                if s.session_date:
                    dates.append(str(s.session_date))
        return list(set(dates))

    def check_asset_conflict(self):
        """Check if any selected asset is already booked on overlapping dates
        in any SUBMITTED booking (not cancelled). Handles Alternative Assets per session."""
        if not self.assets:
            return

        book_requests = []
        default_assets = [d.asset_name for d in self.assets if d.asset_name]
        
        if self.booking_type == "One-time":
            if self.party_date:
                for a in default_assets:
                    book_requests.append((self.party_date, a))
        else:
            for s in self.sessions:
                if not s.session_date: continue
                if getattr(s, "alternative_asset", None):
                    book_requests.append((s.session_date, s.alternative_asset))
                else:
                    for a in default_assets:
                        book_requests.append((s.session_date, a))

        if not book_requests:
            return

        all_dates = list(set([req[0] for req in book_requests]))

        # Existing one-time bookings
        one_time_bookings = frappe.db.sql("""
            SELECT pb.name, pba.asset_name, pb.party_date as conflict_date
            FROM `tabParty Booking` pb
            JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
            WHERE pb.docstatus = 1
            AND pb.name != %(name)s
            AND pb.booking_type = 'One-time'
            AND pb.party_date IN %(dates)s
        """, {"name": self.name or "NEW", "dates": all_dates}, as_dict=True)

        # Existing recurring bookings (using default assets)
        recurring_bookings = frappe.db.sql("""
            SELECT pb.name, pba.asset_name, pbs.session_date as conflict_date
            FROM `tabParty Booking` pb
            JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
            JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
            WHERE pb.docstatus = 1
            AND pb.name != %(name)s
            AND pb.booking_type = 'Recurring'
            AND pbs.session_date IN %(dates)s
            AND (pbs.alternative_asset IS NULL OR pbs.alternative_asset = '')
        """, {"name": self.name or "NEW", "dates": all_dates}, as_dict=True)

        # Existing recurring bookings (using alternative assets)
        recurring_alt_bookings = frappe.db.sql("""
            SELECT pb.name, pbs.alternative_asset as asset_name, pbs.session_date as conflict_date
            FROM `tabParty Booking` pb
            JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
            WHERE pb.docstatus = 1
            AND pb.name != %(name)s
            AND pb.booking_type = 'Recurring'
            AND pbs.session_date IN %(dates)s
            AND pbs.alternative_asset IS NOT NULL
            AND pbs.alternative_asset != ''
        """, {"name": self.name or "NEW", "dates": all_dates}, as_dict=True)

        existing_booked_pairs = {}
        for b in one_time_bookings + recurring_bookings + recurring_alt_bookings:
            existing_booked_pairs[(str(b.conflict_date), b.asset_name)] = b.name

        errors = []
        for req_date, req_asset in book_requests:
            date_str = str(req_date)
            if (date_str, req_asset) in existing_booked_pairs:
                conflict_name = existing_booked_pairs[(date_str, req_asset)]
                errors.append(
                    _("Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2}").format(
                        req_asset, date_str, conflict_name
                    )
                )

        if errors:
            msg = _("The following assets are already booked:") + "<br><br><ul>"
            for err in errors:
                msg += f"<li>{err}</li>"
            msg += "</ul><br>" + _("Please select alternative assets or change the dates for these sessions.")
            frappe.throw(msg, title=_("Asset Conflict"))

    def on_submit(self):
        self.update_asset_status("Booked")

    def on_cancel(self):
        """Revert asset status to Available, but only if it was Booked (not Damaged)."""
        self.update_asset_status_on_cancel()

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
