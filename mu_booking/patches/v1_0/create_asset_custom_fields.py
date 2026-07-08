import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field

def execute():
    if not frappe.db.exists("Custom Field", "Asset-party_booking_status"):
        create_custom_field("Asset", {
            "fieldname": "party_booking_status",
            "label": "Party Booking Status",
            "fieldtype": "Select",
            "options": "Available\nBooked\nDamaged",
            "insert_after": "status",
            "default": "Available"
        })
