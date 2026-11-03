import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

KANBAN_BOARD_NAME = "Party Booking Status"
STATUS_COLUMNS = [
    ("Draft", "Red"),
    ("Confirmed", "Blue"),
    ("Delivery/Installation Scheduled", "Orange"),
    ("Executed", "Purple"),
    ("Pending Return", "Yellow"),
    ("Closed", "Green"),
    ("Cancelled", "Gray"),
]

REQUIRED_ROLES = [
    "Party Booking Officer",
    "Party Booking Manager",
    "Party Installation Manager",
    "Party Accountant",
]


def execute():
    """Ensure roles, custom fields, Property Setters, Kanban Board, and Workspace sync on install/migrate."""
    ensure_roles()
    ensure_asset_custom_fields()
    setup_property_setters()
    setup_kanban_board()
    sync_workspace_and_cache()


def ensure_roles():
    for role_name in REQUIRED_ROLES:
        if not frappe.db.exists("Role", role_name):
            try:
                frappe.get_doc({
                    "doctype": "Role",
                    "role_name": role_name,
                    "desk_access": 1,
                }).insert(ignore_permissions=True)
            except Exception:
                pass


def ensure_asset_custom_fields():
    if not frappe.db.exists("DocType", "Asset"):
        return

    fields_to_create = [
        {
            "fieldname": "party_booking_status",
            "label": "Party Booking Status",
            "fieldtype": "Select",
            "options": "Available\nBooked\nDamaged",
            "insert_after": "status",
            "default": "Available",
            "module": "Mu Booking",
        },
        {
            "fieldname": "asset_booking_status",
            "label": "Asset Booking Status",
            "fieldtype": "Select",
            "options": "Available\nBooked\nDelivered\nDamaged",
            "insert_after": "party_booking_status",
            "default": "Available",
            "in_list_view": 1,
            "in_standard_filter": 1,
            "module": "Mu Booking",
        },
        {
            "fieldname": "current_booking_holder",
            "label": "Current Booking Holder",
            "fieldtype": "Data",
            "insert_after": "asset_booking_status",
            "read_only": 1,
            "no_copy": 1,
            "in_list_view": 1,
            "module": "Mu Booking",
        },
    ]

    for field_def in fields_to_create:
        cf_name = f"Asset-{field_def['fieldname']}"
        if not frappe.db.exists("Custom Field", cf_name):
            try:
                create_custom_field("Asset", field_def)
            except Exception:
                pass


def setup_property_setters():
    try:
        # 1. Customer: show customer_name in Link fields and allow searching by name/mobile
        make_property_setter("Customer", None, "show_title_field_in_link", "1", "Check", for_doctype=True)
        make_property_setter(
            "Customer", None, "search_fields", "customer_name, mobile_no, customer_group", "Data", for_doctype=True
        )

        # 2. Employee: show employee_name in Link fields and allow searching by name/number/mobile
        make_property_setter("Employee", None, "show_title_field_in_link", "1", "Check", for_doctype=True)
        make_property_setter(
            "Employee", None, "search_fields", "employee_name, employee_number, cell_number", "Data", for_doctype=True
        )

        # 3. Asset: make attachments public by default (no Private lock)
        make_property_setter("Asset", None, "make_attachments_public", "1", "Check", for_doctype=True)

        for dt in ("Customer", "Employee", "Asset"):
            frappe.clear_cache(doctype=dt)
    except Exception:
        pass


def setup_kanban_board():
    if not frappe.db.exists("DocType", "Kanban Board"):
        return

    fields_to_show = [
        "customer_name",
        "customer_mobile",
        "party_date",
        "party_day",
        "party_time",
        "party_location",
        "installation_address",
        "installation_manager",
    ]

    try:
        if frappe.db.exists("Kanban Board", KANBAN_BOARD_NAME):
            kb = frappe.get_doc("Kanban Board", KANBAN_BOARD_NAME)
            kb.private = 0
            kb.show_labels = 1
            kb.fields = json.dumps(fields_to_show)
            existing_cols = {c.column_name for c in kb.columns}
            for col_name, indicator in STATUS_COLUMNS:
                if col_name not in existing_cols:
                    kb.append("columns", {"column_name": col_name, "status": "Active", "indicator": indicator})
            kb.save(ignore_permissions=True)
        else:
            kb = frappe.get_doc({
                "doctype": "Kanban Board",
                "kanban_board_name": KANBAN_BOARD_NAME,
                "reference_doctype": "Party Booking",
                "field_name": "status",
                "private": 0,
                "show_labels": 1,
                "fields": json.dumps(fields_to_show),
                "columns": [
                    {"column_name": col_name, "status": "Active", "indicator": indicator}
                    for col_name, indicator in STATUS_COLUMNS
                ],
            })
            kb.insert(ignore_permissions=True)
    except Exception:
        pass


def sync_workspace_and_cache():
    """Mubtkir ERP Master Guidelines (Rule 5): Auto-sync workspace and clear Desk cache on migrate."""
    try:
        frappe.reload_doc("mu_booking", "workspace", "party_bookings", force=True)
        frappe.cache.delete_key("bootinfo")
        frappe.clear_cache()
    except Exception:
        pass
