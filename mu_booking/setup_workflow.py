import frappe

def create_workflow():
    states = [
        "Initial",
        "Pending Officer Review",
        "Confirmed",
        "Delivery/Installation Scheduled",
        "Executed",
        "Pending Return",
        "Closed",
        "Cancelled"
    ]

    actions = [
        "Submit for Review",
        "Confirm",
        "Schedule Delivery",
        "Mark as Executed",
        "Wait for Return",
        "Close Booking",
        "Cancel"
    ]

    for state in states:
        if not frappe.db.exists("Workflow State", state):
            frappe.get_doc({
                "doctype": "Workflow State",
                "workflow_state_name": state
            }).insert(ignore_permissions=True)

    for action in actions:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({
                "doctype": "Workflow Action Master",
                "workflow_action_name": action
            }).insert(ignore_permissions=True)

    if not frappe.db.exists("Workflow", "Party Booking Workflow"):
        doc = frappe.get_doc({
            "doctype": "Workflow",
            "workflow_name": "Party Booking Workflow",
            "document_type": "Party Booking",
            "is_active": 1,
            "states": [
                {"state": "Initial", "doc_status": 0, "allow_edit": "All"},
                {"state": "Pending Officer Review", "doc_status": 0, "allow_edit": "All"},
                {"state": "Confirmed", "doc_status": 1, "allow_edit": "All"},
                {"state": "Delivery/Installation Scheduled", "doc_status": 1, "allow_edit": "All"},
                {"state": "Executed", "doc_status": 1, "allow_edit": "All"},
                {"state": "Pending Return", "doc_status": 1, "allow_edit": "All"},
                {"state": "Closed", "doc_status": 1, "allow_edit": "All"},
                {"state": "Cancelled", "doc_status": 2, "allow_edit": "All"}
            ],
            "transitions": [
                {"state": "Initial", "action": "Submit for Review", "next_state": "Pending Officer Review", "allowed": "All"},
                {"state": "Pending Officer Review", "action": "Confirm", "next_state": "Confirmed", "allowed": "All"},
                {"state": "Confirmed", "action": "Schedule Delivery", "next_state": "Delivery/Installation Scheduled", "allowed": "All"},
                {"state": "Delivery/Installation Scheduled", "action": "Mark as Executed", "next_state": "Executed", "allowed": "All"},
                {"state": "Executed", "action": "Wait for Return", "next_state": "Pending Return", "allowed": "All"},
                {"state": "Pending Return", "action": "Close Booking", "next_state": "Closed", "allowed": "All"},
                {"state": "Pending Officer Review", "action": "Cancel", "next_state": "Cancelled", "allowed": "All"},
                {"state": "Initial", "action": "Cancel", "next_state": "Cancelled", "allowed": "All"}
            ]
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print("Workflow 'Party Booking Workflow' created successfully.")
