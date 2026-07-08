# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _

# Keywords that indicate an asset was damaged during the party
DAMAGE_KEYWORDS = ("تلف", "damage", "broken", "مكسور", "خسر", "lost", "ضائع")


class PartyAssetReturn(Document):
    def validate(self):
        self.validate_booking_is_submitted()   # D05 FIX
        self.validate_no_duplicate_return()    # D04 FIX
        self.validate_refund_amount()
        self.calculate_deduction()

    def validate_booking_is_submitted(self):
        """D05 FIX: Asset Return is only allowed for submitted (confirmed) bookings."""
        if not self.party_booking:
            return
        docstatus = frappe.db.get_value("Party Booking", self.party_booking, "docstatus")
        if docstatus != 1:
            frappe.throw(
                _("Asset Return can only be created for a submitted (confirmed) Party Booking. "
                  "Booking {0} is not yet submitted.").format(self.party_booking)
            )

    def validate_no_duplicate_return(self):
        """D04 FIX: Only one submitted return document is allowed per booking."""
        if not self.party_booking:
            return
        existing = frappe.db.get_value(
            "Party Asset Return",
            {
                "party_booking": self.party_booking,
                "docstatus": 1,           # only submitted returns count
                "name": ["!=", self.name or "NEW"]
            },
            "name"
        )
        if existing:
            frappe.throw(
                _("A submitted Asset Return ({0}) already exists for Booking {1}. "
                  "Cannot create a duplicate.").format(existing, self.party_booking)
            )

    def validate_refund_amount(self):
        """Refund amount cannot exceed the original deposit."""
        original = flt(self.original_deposit)
        refund = flt(self.refund_amount)
        if original > 0 and refund > original:
            frappe.throw(_("Refund Amount ({0}) cannot exceed the Original Deposit ({1}).").format(
                frappe.format(refund, "Currency"),
                frappe.format(original, "Currency")
            ))

    def calculate_deduction(self):
        """Deduction = Original Deposit - Refund Amount (never negative)."""
        self.deduction_amount = max(flt(self.original_deposit) - flt(self.refund_amount), 0)

    def on_submit(self):
        self.release_assets()
        self.close_booking()

    def on_cancel(self):
        self.revert_assets_and_booking()

    def release_assets(self):
        """Set asset status based on deduction reason. If damage keywords found -> Damaged."""
        if not self.party_booking:
            return

        booking = frappe.get_doc("Party Booking", self.party_booking)
        reason_lower = (self.deduction_reason or "").lower()
        is_damaged = any(keyword in reason_lower for keyword in DAMAGE_KEYWORDS)

        for d in booking.assets:
            if d.asset_name:
                new_status = "Damaged" if is_damaged else "Available"
                frappe.db.set_value("Asset", d.asset_name, "party_booking_status", new_status)
                frappe.db.set_value(
                    "Party Booking Asset", d.name, "asset_booking_status",
                    "Damaged" if is_damaged else "Returned"
                )

    def close_booking(self):
        """Update booking deposit status and workflow state to Closed."""
        if not self.party_booking:
            return

        frappe.db.set_value("Party Booking", self.party_booking, {
            "deposit_status": self.refund_status,
            "workflow_state": "Closed"
        })

    def revert_assets_and_booking(self):
        """On cancellation of return doc, revert assets and booking to their previous state."""
        if not self.party_booking:
            return

        booking = frappe.get_doc("Party Booking", self.party_booking)
        for d in booking.assets:
            if d.asset_name:
                frappe.db.set_value("Asset", d.asset_name, "party_booking_status", "Booked")
                frappe.db.set_value("Party Booking Asset", d.name, "asset_booking_status", "Booked")

        frappe.db.set_value("Party Booking", self.party_booking, {
            "deposit_status": "Pending",
            "workflow_state": "Pending Return"
        })
