import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

# Show employee names instead of IDs in Link fields, and allow searching
# employees by name, number and mobile
PROPERTIES = [
    ("show_title_field_in_link", "1", "Check"),
    ("search_fields", "employee_name, employee_number, cell_number", "Data"),
]


def execute():
    for prop, value, prop_type in PROPERTIES:
        make_property_setter("Employee", None, prop, value, prop_type, for_doctype=True)
        ps_name = frappe.db.get_value(
            "Property Setter", {"doc_type": "Employee", "property": prop}, "name"
        )
        if ps_name:
            frappe.db.set_value("Property Setter", ps_name, "module", "Mu Booking", update_modified=False)

    frappe.clear_cache(doctype="Employee")
