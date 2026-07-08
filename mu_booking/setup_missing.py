import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_missing():
    # 1. Create Roles
    roles = ["Party Booking Officer", "Party Installation Manager", "Party Accountant"]
    for role in roles:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role,
                "desk_access": 1
            }).insert(ignore_permissions=True)

    # 2. Add Missing Fields to Party Booking
    custom_fields = {
        "Party Booking": [
            {"fieldname": "installation_section", "fieldtype": "Section Break", "label": "Installation Details", "insert_after": "booking_officer"},
            {"fieldname": "delivery_time", "fieldtype": "Time", "label": "Delivery Time"},
            {"fieldname": "execution_duration", "fieldtype": "Data", "label": "Execution Duration (e.g. 2 Hours)"},
            {"fieldname": "number_of_workers", "fieldtype": "Int", "label": "Number of Workers"},
            {"fieldname": "cb_install", "fieldtype": "Column Break"},
            {"fieldname": "delivery_vehicle", "fieldtype": "Data", "label": "Delivery Vehicle/Car"},
            {"fieldname": "installation_team", "fieldtype": "Small Text", "label": "Installation Team"}
        ]
    }
    create_custom_fields(custom_fields, ignore_validate=True)

    # 3. Update Workflow with Roles
    if frappe.db.exists("Workflow", "Party Booking Workflow"):
        wf = frappe.get_doc("Workflow", "Party Booking Workflow")
        
        for state in wf.states:
            state.allow_edit = "System Manager"
            if state.state in ["Initial", "Pending Officer Review"]:
                state.allow_edit = "Party Booking Officer"
            elif state.state in ["Confirmed", "Delivery/Installation Scheduled", "Executed"]:
                state.allow_edit = "Party Installation Manager"
            elif state.state in ["Pending Return", "Closed"]:
                state.allow_edit = "Party Accountant"
            
        for t in wf.transitions:
            t.allowed = "System Manager"
            if t.action == "Submit for Review":
                t.allowed = "Guest" # AI Bot or Guest
            elif t.action in ["Confirm", "Cancel"]:
                t.allowed = "Party Booking Officer"
            elif t.action in ["Schedule Delivery", "Mark as Executed", "Wait for Return"]:
                t.allowed = "Party Installation Manager"
            elif t.action == "Close Booking":
                t.allowed = "Party Accountant"
                
        wf.save(ignore_permissions=True)

    # 4. Create Webhooks
    webhooks = [
        {"name": "Party Booking Request Received", "condition": "doc.workflow_state == 'Initial'", "event": "on_update"},
        {"name": "Party Booking Confirmed", "condition": "doc.workflow_state == 'Confirmed'", "event": "on_update"},
        {"name": "Party Booking Executed", "condition": "doc.workflow_state == 'Executed'", "event": "on_update"},
    ]
    for w in webhooks:
        if not frappe.db.exists("Webhook", {"webhook_name": w["name"]}):
            frappe.get_doc({
                "doctype": "Webhook",
                "webhook_docevent": w["event"],
                "webhook_doctype": "Party Booking",
                "webhook_name": w["name"],
                "condition": w["condition"],
                "request_url": "https://n8n.yourserver.com/webhook/party-booking",
                "request_method": "POST"
            }).insert(ignore_permissions=True)

    frappe.db.commit()
    print("Setup of missing items complete.")

