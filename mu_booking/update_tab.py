import frappe


def fix_installation_tab():
    if frappe.db.exists("Custom Field", "Party Booking-installation_section"):
        frappe.delete_doc("Custom Field", "Party Booking-installation_section", ignore_permissions=True)
        frappe.db.commit()


if __name__ == "__main__":
    fix_installation_tab()
