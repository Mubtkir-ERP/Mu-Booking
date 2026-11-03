import frappe


def fix_ui_issues():
    if not frappe.db.exists("Custom Field", "Asset-party_booking_status"):
        doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Asset",
            "fieldname": "party_booking_status",
            "label": "Party Booking Status",
            "fieldtype": "Select",
            "options": "Available\nBooked\nDamaged",
            "insert_after": "status",
            "default": "Available",
        })
        doc.insert(ignore_permissions=True)
    frappe.db.commit()


if __name__ == "__main__":
    fix_ui_issues()
