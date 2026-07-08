import frappe
import json

def update_workspace():
    workspace_name = "Party Bookings"
    
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
    else:
        doc = frappe.new_doc("Workspace")
        doc.title = workspace_name
        doc.label = workspace_name
        doc.name = workspace_name
        doc.module = "Mu Booking"
        doc.is_standard = 1
        doc.public = 1
        doc.icon = "calender"
        doc.insert(ignore_permissions=True)

    # Clear existing child tables
    doc.shortcuts = []
    doc.links = []
    
    # 1. Add Shortcuts
    shortcuts_data = [
        {"label": "Party Booking", "type": "DocType", "link_to": "Party Booking"},
        {"label": "Party Asset Return", "type": "DocType", "link_to": "Party Asset Return"},
        {"label": "Assets", "type": "DocType", "link_to": "Asset"},
        {"label": "Asset Utilization Report", "type": "Report", "link_to": "Asset Utilization Report"}
    ]
    
    for s in shortcuts_data:
        doc.append("shortcuts", s)
        
    # 2. Add Links (Cards)
    links_data = [
        {"label": "Transactions", "type": "Card Break", "link_type": "DocType", "link_to": ""},
        {"label": "Party Booking", "type": "Link", "link_type": "DocType", "link_to": "Party Booking"},
        {"label": "Party Asset Return", "type": "Link", "link_type": "DocType", "link_to": "Party Asset Return"},
        
        {"label": "Settings & Masters", "type": "Card Break", "link_type": "DocType", "link_to": ""},
        {"label": "Assets", "type": "Link", "link_type": "DocType", "link_to": "Asset"},
        
        {"label": "Reports", "type": "Card Break", "link_type": "Report", "link_to": ""},
        {"label": "Party Bookings Report", "type": "Link", "link_type": "Report", "link_to": "Party Bookings Report"},
        {"label": "Asset Utilization Report", "type": "Link", "link_type": "Report", "link_to": "Asset Utilization Report"},
        {"label": "Security Deposit Report", "type": "Link", "link_type": "Report", "link_to": "Security Deposit Report"},
        {"label": "Installation & Delivery Report", "type": "Link", "link_type": "Report", "link_to": "Installation & Delivery Report"},
        {"label": "Damaged and Lost Assets Report", "type": "Link", "link_type": "Report", "link_to": "Damaged and Lost Assets Report"}
    ]
    
    for l in links_data:
        doc.append("links", l)
        
    # 3. Build Content JSON
    content_blocks = [
        {
            "type": "header",
            "data": {
                "text": "Party Booking System",
                "level": 2,
                "col": 12
            }
        }
    ]
    
    # Add Shortcuts to content
    for s in shortcuts_data:
        content_blocks.append({
            "type": "shortcut",
            "data": {
                "shortcut_name": s["label"],
                "col": 3
            }
        })
        
    # Add Spacer
    content_blocks.append({
        "type": "spacer",
        "data": {
            "col": 12
        }
    })
    
    # Add Header for cards
    content_blocks.append({
        "type": "header",
        "data": {
            "text": "Masters & Reports",
            "level": 3,
            "col": 12
        }
    })
    
    # Add Link Cards to content
    for l in links_data:
        if l["type"] == "Card Break":
            content_blocks.append({
                "type": "card",
                "data": {
                    "card_name": l["label"],
                    "col": 4
                }
            })
            
    doc.content = json.dumps(content_blocks)
    
    # Save the document
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    print("Workspace successfully populated with all App components!")

