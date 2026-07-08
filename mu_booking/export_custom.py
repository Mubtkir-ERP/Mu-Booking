import frappe

def execute():
    try:
        custom_docs = frappe.get_all("DocType", filters={"custom": 1, "module": "Mu Booking"})
        if not custom_docs:
            # Let's also check if they created it without assigning a module
            custom_docs = frappe.get_all("DocType", filters={"custom": 1, "name": "Event Type"})
            
        count = 0
        for d in custom_docs:
            doc = frappe.get_doc("DocType", d.name)
            doc.custom = 0
            doc.module = "Mu Booking"
            doc.save(ignore_permissions=True)
            count += 1
            
        frappe.db.commit()
        return {"status": "success", "message": f"Exported {count} custom DocTypes successfully!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
