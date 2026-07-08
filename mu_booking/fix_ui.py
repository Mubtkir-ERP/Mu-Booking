import frappe

def fix_ui_issues():
    # 1. Re-create party_booking_status on Asset if missing
    if not frappe.db.exists("Custom Field", "Asset-party_booking_status"):
        doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Asset",
            "fieldname": "party_booking_status",
            "label": "Party Booking Status",
            "fieldtype": "Select",
            "options": "Available\nBooked\nDamaged",
            "insert_after": "status",
            "default": "Available"
        })
        doc.insert(ignore_permissions=True)
        print("Re-created party_booking_status field in Asset.")
    else:
        print("party_booking_status already exists in Asset.")

    # 2. Move installation_tab to the end
    if frappe.db.exists("Custom Field", "Party Booking-installation_tab"):
        doc = frappe.get_doc("Custom Field", "Party Booking-installation_tab")
        doc.insert_after = "amended_from" # This is the last standard field in Party Booking
        doc.save(ignore_permissions=True)
        print("Moved installation_tab to the end.")

    # 3. Fix the sequence of the custom fields to fall under installation_tab
    field_sequence = [
        ("delivery_time", "installation_tab"),
        ("execution_duration", "delivery_time"),
        ("number_of_workers", "execution_duration"),
        ("cb_install", "number_of_workers"),
        ("delivery_vehicle", "cb_install"),
        ("installation_team", "delivery_vehicle")
    ]

    for fieldname, insert_after in field_sequence:
        custom_field_name = f"Party Booking-{fieldname}"
        if frappe.db.exists("Custom Field", custom_field_name):
            f_doc = frappe.get_doc("Custom Field", custom_field_name)
            f_doc.insert_after = insert_after
            f_doc.save(ignore_permissions=True)
            print(f"Updated insert_after for {fieldname} -> {insert_after}")

    frappe.db.commit()
    print("UI Fixes applied successfully.")

fix_ui_issues()
