import frappe

def apply_updates():
    # 1. Create Event Type Doctype
    if not frappe.db.exists("DocType", "Event Type"):
        doc = frappe.get_doc({
            "doctype": "DocType",
            "name": "Event Type",
            "module": "Mu Booking",
            "custom": 1,
            "autoname": "field:event_name",
            "fields": [
                {"fieldname": "event_name", "fieldtype": "Data", "label": "Event Name", "reqd": 1, "unique": 1}
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1},
                {"role": "Party Booking Officer", "read": 1, "write": 1, "create": 1, "delete": 1}
            ]
        })
        doc.insert(ignore_permissions=True)
        # Create default events
        for e in ["زفاف", "خطوبة", "عيد ميلاد", "تخرج", "حفلة خاصة"]:
            if not frappe.db.exists("Event Type", e):
                frappe.get_doc({"doctype": "Event Type", "event_name": e}).insert(ignore_permissions=True)
        print("Event Type Doctype created.")
        
    # 2. Update Party Booking doctype field 'event_type'
    pb = frappe.get_doc("DocType", "Party Booking")
    changed = False
    for f in pb.fields:
        if f.fieldname == "event_type":
            if f.fieldtype != "Link":
                f.fieldtype = "Link"
                f.options = "Event Type"
                changed = True
    if changed:
        pb.save(ignore_permissions=True)
        print("Party Booking event_type updated to Link.")

    # 3. Simplify Workflow (Employee driven)
    states = ["Draft", "Confirmed", "Delivery/Installation Scheduled", "Executed", "Pending Return", "Closed", "Cancelled"]
    for state in states:
        if not frappe.db.exists("Workflow State", state):
            frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": state}).insert(ignore_permissions=True)
            
    if frappe.db.exists("Workflow", "Party Booking Workflow"):
        wf = frappe.get_doc("Workflow", "Party Booking Workflow")
        
        # Set all states properly
        wf.states = []
        wf.append("states", {"state": "Draft", "doc_status": 0, "allow_edit": "Party Booking Officer"})
        wf.append("states", {"state": "Confirmed", "doc_status": 1, "allow_edit": "Party Installation Manager"})
        wf.append("states", {"state": "Delivery/Installation Scheduled", "doc_status": 1, "allow_edit": "Party Installation Manager"})
        wf.append("states", {"state": "Executed", "doc_status": 1, "allow_edit": "Party Installation Manager"})
        wf.append("states", {"state": "Pending Return", "doc_status": 1, "allow_edit": "System Manager"})
        wf.append("states", {"state": "Closed", "doc_status": 1, "allow_edit": "System Manager"})
        wf.append("states", {"state": "Cancelled", "doc_status": 2, "allow_edit": "System Manager"})
                
        # Simplify transitions: Draft -> Confirmed
        wf.transitions = []
        wf.append("transitions", {"state": "Draft", "action": "Confirm", "next_state": "Confirmed", "allowed": "Party Booking Officer"})
        wf.append("transitions", {"state": "Confirmed", "action": "Schedule Delivery", "next_state": "Delivery/Installation Scheduled", "allowed": "Party Installation Manager"})
        wf.append("transitions", {"state": "Delivery/Installation Scheduled", "action": "Mark as Executed", "next_state": "Executed", "allowed": "Party Installation Manager"})
        wf.append("transitions", {"state": "Executed", "action": "Wait for Return", "next_state": "Pending Return", "allowed": "Party Installation Manager"})
        wf.append("transitions", {"state": "Pending Return", "action": "Close Booking", "next_state": "Closed", "allowed": "System Manager"})
        wf.append("transitions", {"state": "Confirmed", "action": "Cancel", "next_state": "Cancelled", "allowed": "Party Booking Officer"})

        wf.save(ignore_permissions=True)
        print("Workflow updated for employee usage.")

    frappe.db.commit()
    print("All updates applied successfully.")
