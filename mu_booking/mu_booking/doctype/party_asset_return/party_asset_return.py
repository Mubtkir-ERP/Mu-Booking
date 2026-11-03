# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from mu_booking.mu_booking.doctype.party_booking.party_booking import (
    STATUS_CLOSED,
    STATUS_PENDING_RETURN,
    get_active_bookings_holding,
)

# Keywords that indicate an asset was damaged during the party
DAMAGE_KEYWORDS = ("تلف", "damage", "broken", "مكسور", "خسر", "lost", "ضائع")


class PartyAssetReturn(Document):
    def validate(self):
        self.validate_booking_is_pending_return()
        self.validate_no_duplicate_return()  # D04 FIX
        self.validate_refund_amount()
        self.calculate_deduction()

    def validate_booking_is_pending_return(self):
        """Asset Return is only allowed once the booking is waiting for its assets back."""
        if not self.party_booking:
            return
        booking = frappe.db.get_value(
            "Party Booking", self.party_booking, ["docstatus", "status"], as_dict=True
        )
        if not booking or booking.docstatus != 1 or booking.status != STATUS_PENDING_RETURN:
            frappe.throw(
                _("Asset Return can only be created when Booking {0} is in status {1}.").format(
                    self.party_booking, _(STATUS_PENDING_RETURN)
                )
            )

    def validate_no_duplicate_return(self):
        """D04 FIX: Only one submitted return document is allowed per booking."""
        if not self.party_booking:
            return
        existing = frappe.db.get_value(
            "Party Asset Return",
            {
                "party_booking": self.party_booking,
                "docstatus": 1,  # only submitted returns count
                "name": ["!=", self.name or "NEW"],
            },
            "name",
        )
        if existing:
            frappe.throw(
                _(
                    "A submitted Asset Return ({0}) already exists for Booking {1}. "
                    "Cannot create a duplicate."
                ).format(existing, self.party_booking)
            )

    def validate_refund_amount(self):
        """Refund amount cannot exceed the original deposit."""
        original = flt(self.original_deposit)
        refund = flt(self.refund_amount)
        if original > 0 and refund > original:
            frappe.throw(
                _("Refund Amount ({0}) cannot exceed the Original Deposit ({1}).").format(
                    frappe.format(refund, "Currency"),
                    frappe.format(original, "Currency"),
                )
            )

    def calculate_deduction(self):
        """Deduction = Original Deposit - Refund Amount (never negative)."""
        self.deduction_amount = max(flt(self.original_deposit) - flt(self.refund_amount), 0)

    def before_submit(self):
        allowed_roles = {"Party Accountant", "Party Booking Manager", "System Manager"}
        user_roles = set(frappe.get_roles(frappe.session.user))
        if frappe.session.user != "Administrator" and not (user_roles & allowed_roles):
            frappe.throw(
                _("Only the Accountant or Booking Manager can submit an Asset Return."),
                frappe.PermissionError,
            )

    def on_submit(self):
        self.release_assets()
        self.close_booking()

    def on_cancel(self):
        self.revert_assets_and_booking()

    def release_assets(self):
        """Release main and alternative assets. Only mark specific assets as Damaged."""
        if not self.party_booking:
            return

        booking = frappe.get_doc("Party Booking", self.party_booking)
        reason_lower = (self.deduction_reason or "").lower()
        has_damage_keyword = any(keyword in reason_lower for keyword in DAMAGE_KEYWORDS)
        single_asset_booking = len([d for d in booking.assets if d.asset_name]) == 1

        for d in booking.assets:
            if d.asset_name:
                # Mark as Damaged only if explicitly marked on the asset row,
                # if its asset_name/title is mentioned in deduction_reason,
                # or if there is only 1 asset in the booking and damage keywords exist.
                explicitly_damaged = (
                    d.asset_booking_status == "Damaged"
                    or (
                        has_damage_keyword
                        and (
                            single_asset_booking
                            or d.asset_name.lower() in reason_lower
                            or (d.asset_title and d.asset_title.lower() in reason_lower)
                        )
                    )
                )
                if explicitly_damaged:
                    frappe.db.set_value("Asset", d.asset_name, "party_booking_status", "Damaged")
                    frappe.db.set_value("Party Booking Asset", d.name, "asset_booking_status", "Damaged")
                else:
                    other_active = get_active_bookings_holding([d.asset_name], exclude=booking.name)
                    new_master_status = "Booked" if other_active.get(d.asset_name) else "Available"
                    frappe.db.set_value("Asset", d.asset_name, "party_booking_status", new_master_status)
                    frappe.db.set_value("Party Booking Asset", d.name, "asset_booking_status", "Returned")

        # Also release alternative_asset in recurring sessions
        for s in booking.sessions or []:
            alt_asset = getattr(s, "alternative_asset", None)
            if alt_asset:
                current_status = frappe.db.get_value("Asset", alt_asset, "party_booking_status")
                if current_status != "Damaged":
                    other_active = get_active_bookings_holding([alt_asset], exclude=booking.name)
                    new_master_status = "Booked" if other_active.get(alt_asset) else "Available"
                    frappe.db.set_value("Asset", alt_asset, "party_booking_status", new_master_status)

    def close_booking(self):
        """Close the booking and record the final deposit status."""
        if not self.party_booking:
            return
        booking = frappe.get_doc("Party Booking", self.party_booking)
        deposit_status_map = {
            "Completed": "Refunded",
            "Partially Deducted": "Partially Deducted",
            "Pending": "Pending",
        }
        mapped_deposit_status = deposit_status_map.get(self.refund_status, "Refunded")
        booking.set_status(STATUS_CLOSED, deposit_status=mapped_deposit_status)

    def revert_assets_and_booking(self):
        """On cancellation of return doc, revert assets and booking to their previous state."""
        if not self.party_booking:
            return

        booking = frappe.get_doc("Party Booking", self.party_booking)
        for d in booking.assets:
            if d.asset_name:
                frappe.db.set_value("Asset", d.asset_name, "party_booking_status", "Booked")
                frappe.db.set_value("Party Booking Asset", d.name, "asset_booking_status", "Booked")

        for s in booking.sessions or []:
            alt_asset = getattr(s, "alternative_asset", None)
            if alt_asset:
                frappe.db.set_value("Asset", alt_asset, "party_booking_status", "Booked")

        booking.set_status(STATUS_PENDING_RETURN, deposit_status="Pending")
