import frappe


def fix_reports():
    workspace_name = "Party Bookings"
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        for link in doc.links:
            if link.link_type == "Report":
                if "Installation" in link.link_to:
                    if frappe.db.exists("Report", "Installation and Delivery Report"):
                        link.link_to = "Installation and Delivery Report"
                    elif frappe.db.exists("Report", "Installation & Delivery Report"):
                        link.link_to = "Installation & Delivery Report"
        doc.save(ignore_permissions=True)

    reports = frappe.get_all(
        "Report", filters={"module": "Mu Booking"}, fields=["name", "report_type", "is_standard"]
    )
    for r in reports:
        doc = frappe.get_doc("Report", r.name)
        if doc.report_type != "Script Report":
            doc.report_type = "Script Report"
            doc.is_standard = "Yes"
            doc.save(ignore_permissions=True)

    frappe.db.commit()


if __name__ == "__main__":
    fix_reports()
