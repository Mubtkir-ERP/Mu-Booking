import frappe
from frappe.model.utils.rename_field import rename_field

OLD_FIELD = "booking_officer"
NEW_FIELD = "installation_manager"


def execute():
    """Rename the employee field on Party Booking (the officer became the installation manager)."""
    frappe.reload_doc("mu_booking", "doctype", "party_booking")

    if frappe.db.has_column("Party Booking", OLD_FIELD):
        rename_field("Party Booking", OLD_FIELD, NEW_FIELD)

    # Keep site-level custom fields anchored to the renamed field
    frappe.db.set_value(
        "Custom Field", {"dt": "Party Booking", "insert_after": OLD_FIELD},
        "insert_after", NEW_FIELD, update_modified=False,
    )
