import frappe

def create_reports():
    reports = [
        {"name": "Party Bookings Report", "ref_doctype": "Party Booking"},
        {"name": "Asset Utilization Report", "ref_doctype": "Asset"},
        {"name": "Security Deposit Report", "ref_doctype": "Party Asset Return"},
        {"name": "Installation and Delivery Report", "ref_doctype": "Party Booking"},
        {"name": "Damaged and Lost Assets Report", "ref_doctype": "Party Asset Return"}
    ]
    
    for r in reports:
        if not frappe.db.exists("Report", r["name"]):
            doc = frappe.get_doc({
                "doctype": "Report",
                "report_name": r["name"],
                "ref_doctype": r["ref_doctype"],
                "report_type": "Script Report",
                "is_standard": "Yes",
                "module": "Mu Booking"
            })
            doc.insert(ignore_permissions=True)
            print(f"Created Report: {r['name']}")
        else:
            print(f"Report already exists: {r['name']}")

    frappe.db.commit()
    print("Reports creation complete.")
