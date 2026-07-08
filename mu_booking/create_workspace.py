import frappe
import json

def create_workspace():
    workspace_name = "Party Bookings"
    if not frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc({
            "doctype": "Workspace",
            "title": workspace_name,
            "label": workspace_name,
            "name": workspace_name,
            "module": "Mu Booking",
            "is_standard": 1,
            "public": 1,
            "icon": "calender",
            "content": json.dumps([
                {
                    "type": "header",
                    "data": {
                        "text": "Party Booking System",
                        "level": 2,
                        "col": 12
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Party Booking",
                        "col": 4
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Party Asset Return",
                        "col": 4
                    }
                },
                {
                    "type": "shortcut",
                    "data": {
                        "shortcut_name": "Assets",
                        "col": 4
                    }
                }
            ])
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Workspace '{workspace_name}' created successfully.")
    else:
        print(f"Workspace '{workspace_name}' already exists.")
