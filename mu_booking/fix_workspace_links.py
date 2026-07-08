import frappe
import json

def fix_workspace():
    workspace_name = "Party Bookings"
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        changed = False
        
        for l in doc.links:
            if l.link_to == "Installation & Delivery Report":
                l.link_to = "Installation and Delivery Report"
                l.label = "Installation and Delivery Report"
                changed = True
                
        if doc.content:
            try:
                content = json.loads(doc.content)
                for block in content:
                    if block.get("type") == "shortcut" and block["data"].get("shortcut_name") == "Installation & Delivery Report":
                        block["data"]["shortcut_name"] = "Installation and Delivery Report"
                        changed = True
                doc.content = json.dumps(content)
            except Exception:
                pass
                
        if changed:
            doc.save(ignore_permissions=True)
            frappe.db.commit()
            print("Workspace links updated successfully.")
        else:
            print("No links needed updating.")

fix_workspace()
