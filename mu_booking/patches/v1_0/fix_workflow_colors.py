import frappe

def execute():
    # Fix Workflow State colors automatically when migrating on server
    frappe.db.sql("UPDATE `tabWorkflow State` SET style='Danger' WHERE name='Draft'")
    frappe.db.sql("UPDATE `tabWorkflow State` SET style='Success' WHERE name='Closed' OR name='Completed' OR name='Approved'")
    frappe.db.sql("UPDATE `tabWorkflow State` SET style='Warning' WHERE name='Pending' OR name='Review'")
    frappe.db.sql("UPDATE `tabWorkflow State` SET style='Inverse' WHERE name='Cancelled' OR name='Rejected'")
    frappe.db.sql("UPDATE `tabWorkflow State` SET style='Primary' WHERE name='Submitted'")
    
    frappe.db.commit()
