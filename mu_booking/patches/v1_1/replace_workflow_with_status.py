import frappe

WORKFLOW_NAME = "Party Booking Workflow"
WORKFLOW_FIELD = "Party Booking-workflow_state"

# Legacy workflow states that no longer exist as booking statuses
STATE_MAP = {
    "Initial": "Draft",
    "Pending Officer Review": "Draft",
    "Approved": "Confirmed",
}
VALID_STATUSES = {
    "Draft", "Confirmed", "Delivery/Installation Scheduled",
    "Executed", "Pending Return", "Closed", "Cancelled",
}


def execute():
    """Migrate Party Booking from the Workflow engine to the plain `status` field."""
    frappe.reload_doc("mu_booking", "doctype", "party_booking")

    if frappe.db.has_column("Party Booking", "workflow_state"):
        bookings = frappe.db.sql(
            "SELECT name, docstatus, workflow_state FROM `tabParty Booking`", as_dict=True
        )
        for booking in bookings:
            frappe.db.set_value(
                "Party Booking", booking.name, "status",
                resolve_status(booking), update_modified=False,
            )

    for doctype, name in (("Workflow", WORKFLOW_NAME), ("Custom Field", WORKFLOW_FIELD)):
        if frappe.db.exists(doctype, name):
            frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)

    frappe.clear_cache(doctype="Party Booking")


def resolve_status(booking):
    if booking.docstatus == 2:
        return "Cancelled"
    if booking.docstatus == 0:
        return "Draft"
    status = STATE_MAP.get(booking.workflow_state, booking.workflow_state)
    return status if status in VALID_STATUSES else "Confirmed"
