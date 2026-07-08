import frappe

def fix_installation_tab():
    # 1. Delete the old Section Break
    if frappe.db.exists("Custom Field", "Party Booking-installation_section"):
        frappe.delete_doc("Custom Field", "Party Booking-installation_section", ignore_permissions=True)
        print("Deleted old installation_section")

    # 2. Add the new Tab Break for Installation Details
    if not frappe.db.exists("Custom Field", "Party Booking-installation_tab"):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Party Booking",
            "fieldname": "installation_tab",
            "fieldtype": "Tab Break",
            "label": "Installation Details",
            "insert_after": "booking_officer"
        })
        custom_field.insert(ignore_permissions=True)
        print("Added new installation_tab")

    # 3. Add a Tab Break at the very beginning for the main details
    if not frappe.db.exists("Custom Field", "Party Booking-main_details_tab"):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Party Booking",
            "fieldname": "main_details_tab",
            "fieldtype": "Tab Break",
            "label": "Booking Details",
            "insert_after": ""  # Insert at the very top
        })
        custom_field.insert(ignore_permissions=True)
        print("Added Booking Details Tab at the top")

    frappe.db.commit()

fix_installation_tab()
