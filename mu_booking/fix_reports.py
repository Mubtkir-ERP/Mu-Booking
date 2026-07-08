import frappe

def fix_reports():
    # Fix the workspace links to use the correct report names
    workspace_name = "Party Bookings"
    if frappe.db.exists("Workspace", workspace_name):
        doc = frappe.get_doc("Workspace", workspace_name)
        for link in doc.links:
            if link.link_type == "Report":
                # Ensure the link_to matches the actual report name
                if "Installation" in link.link_to:
                    # Let's check which one exists in DB
                    if frappe.db.exists("Report", "Installation and Delivery Report"):
                        link.link_to = "Installation and Delivery Report"
                    elif frappe.db.exists("Report", "Installation & Delivery Report"):
                        link.link_to = "Installation & Delivery Report"
        doc.save(ignore_permissions=True)
        print("Fixed workspace report links")

    # Now fix the Report types
    reports = frappe.get_all("Report", filters={"module": "Mu Booking"}, fields=["name", "report_type", "is_standard"])
    for r in reports:
        doc = frappe.get_doc("Report", r.name)
        if doc.report_type != "Script Report":
            print(f"Fixing {r.name}: changing from {doc.report_type} to Script Report")
            doc.report_type = "Script Report"
            doc.is_standard = "Yes"
            doc.save(ignore_permissions=True)
                
    frappe.db.commit()
    print("All reports fixed!")

fix_reports()
