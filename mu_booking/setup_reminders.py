import frappe

def create_reminder_doctype():
    if not frappe.db.exists("DocType", "Party Booking Reminder"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Party Booking Reminder",
            "module": "Mu Booking",
            "custom": 1,
            "autoname": "format:REM-{YYYY}-{MM}-{####}",
            "is_submittable": 0,
            "fields": [
                {"fieldname": "booking", "fieldtype": "Link", "options": "Party Booking", "label": "Booking", "in_list_view": 1, "reqd": 1, "read_only": 1},
                {"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name", "in_list_view": 1, "read_only": 1, "fetch_from": "booking.customer_name"},
                {"fieldname": "customer_mobile", "fieldtype": "Data", "label": "Customer Mobile", "in_list_view": 1, "read_only": 1, "fetch_from": "booking.customer_mobile"},
                {"fieldname": "party_date", "fieldtype": "Date", "label": "Party Date", "in_list_view": 1, "read_only": 1, "fetch_from": "booking.party_date"},
                {"fieldname": "party_time", "fieldtype": "Time", "label": "Party Time", "read_only": 1, "fetch_from": "booking.party_time"},
                {"fieldname": "reminder_status", "fieldtype": "Select", "label": "Status", "options": "Triggered", "default": "Triggered", "in_list_view": 1}
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
                {"role": "Party Booking Officer", "read": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Party Booking Reminder DocType created successfully.")
    else:
        print("DocType already exists.")

create_reminder_doctype()
