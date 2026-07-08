# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import add_days, getdate, today
from frappe import _


class PartyBooking(Document):
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
        """C03 FIX: Validate that recurring bookings have at least 1 day/session."""
        if self.booking_type == "Recurring":
            if not self.recurring_pattern:
                frappe.throw(_("Please select a Recurring Pattern for a Recurring booking."))
            if self.recurring_pattern == "Daily":
                if not self.number_of_days or int(self.number_of_days) < 1:
                    frappe.throw(_("Number of Days/Sessions must be at least 1 for a Daily recurring booking."))
                if not self.start_date:
                    frappe.throw(_("Start Date is required for a Daily recurring booking."))

    def generate_recurring_sessions(self):
        """Auto-generate sessions for Recurring bookings with Daily pattern.
        Only generates if sessions table is empty to avoid overwriting manual edits.
        Clears and regenerates if start_date or number_of_days changed.
        """
        if self.booking_type != "Recurring" or not self.recurring_pattern:
            return

        if self.recurring_pattern == "Daily" and self.start_date and self.number_of_days:
            # Check if we need to regenerate (no sessions yet, or date/count changed)
            needs_regenerate = not self.sessions
            if not needs_regenerate and not self.is_new():
                old_doc = self.get_doc_before_save()
                if old_doc:
                    if (str(old_doc.start_date) != str(self.start_date) or
                            old_doc.number_of_days != self.number_of_days):
                        needs_regenerate = True

            if needs_regenerate:
                self.sessions = []
                for i in range(self.number_of_days):
                    self.append("sessions", {
                        "session_date": add_days(self.start_date, i),
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
        in any SUBMITTED or DRAFT booking (not cancelled)."""
        if not self.assets:
            return

        dates = self.get_booking_dates()
        if not dates:
            return

        asset_names = [d.asset_name for d in self.assets if d.asset_name]
        if not asset_names:
            return

        # Check conflicts with submitted one-time bookings
        one_time_conflicts = frappe.db.sql("""
            SELECT pb.name, pba.asset_name, pb.party_date as conflict_date
            FROM `tabParty Booking` pb
            JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
            WHERE pb.docstatus = 1
            AND pb.name != %(name)s
            AND pb.booking_type = 'One-time'
            AND pb.party_date IN %(dates)s
            AND pba.asset_name IN %(assets)s
        """, {"name": self.name or "NEW", "dates": dates, "assets": asset_names}, as_dict=True)

        if one_time_conflicts:
            c = one_time_conflicts[0]
            frappe.throw(
                _("Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2}").format(
                    c.asset_name, c.conflict_date, c.name
                )
            )

        # Check conflicts with submitted recurring bookings
        recurring_conflicts = frappe.db.sql("""
            SELECT pb.name, pba.asset_name, pbs.session_date as conflict_date
            FROM `tabParty Booking` pb
            JOIN `tabParty Booking Asset` pba ON pba.parent = pb.name
            JOIN `tabParty Booking Session` pbs ON pbs.parent = pb.name
            WHERE pb.docstatus = 1
            AND pb.name != %(name)s
            AND pb.booking_type = 'Recurring'
            AND pbs.session_date IN %(dates)s
            AND pba.asset_name IN %(assets)s
        """, {"name": self.name or "NEW", "dates": dates, "assets": asset_names}, as_dict=True)

        if recurring_conflicts:
            c = recurring_conflicts[0]
            frappe.throw(
                _("Asset <b>{0}</b> is already booked on <b>{1}</b> in Recurring Booking {2}").format(
                    c.asset_name, c.conflict_date, c.name
                )
            )

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

    def update_asset_status_on_cancel(self):
        """On cancellation, revert only assets that are still 'Booked' (not Damaged)."""
        for d in self.assets:
            if d.asset_name:
                current_status = frappe.db.get_value("Asset", d.asset_name, "party_booking_status")
                if current_status == "Booked":
                    frappe.db.set_value("Asset", d.asset_name, "party_booking_status", "Available")
                    d.db_set("asset_booking_status", "Available")
