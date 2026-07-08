import frappe

def execute():
    try:
        doc = frappe.get_doc("DocType", "Event Type")
        doc.custom = 0
        doc.module = "Mu Booking"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return "Event Type DocType successfully exported to the app!"
    except Exception as e:
        return f"Error: {str(e)}"
