import frappe

def create_reports():
    reports = [
        {
            "report_name": "Party Bookings Report",
            "ref_doctype": "Party Booking",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Mu Booking"
        },
        {
            "report_name": "Asset Utilization Report",
            "ref_doctype": "Party Booking Asset",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Mu Booking"
        },
        {
            "report_name": "Security Deposit Report",
            "ref_doctype": "Party Booking",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Mu Booking"
        },
        {
            "report_name": "Installation & Delivery Report",
            "ref_doctype": "Party Booking",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Mu Booking"
        },
        {
            "report_name": "Damaged and Lost Assets Report",
            "ref_doctype": "Party Asset Return",
            "report_type": "Report Builder",
            "is_standard": "Yes",
            "module": "Mu Booking"
        }
    ]

    for r in reports:
        if not frappe.db.exists("Report", r["report_name"]):
            frappe.get_doc({
                "doctype": "Report",
                "report_name": r["report_name"],
                "ref_doctype": r["ref_doctype"],
                "report_type": r["report_type"],
                "is_standard": r["is_standard"],
                "module": r["module"]
            }).insert(ignore_permissions=True)
            print(f"Report '{r['report_name']}' created.")

    frappe.db.commit()
