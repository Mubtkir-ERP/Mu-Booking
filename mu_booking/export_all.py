import frappe

def execute():
    cf_name = "Asset-party_booking_status"
    if frappe.db.exists("Custom Field", cf_name):
        frappe.db.set_value("Custom Field", cf_name, "module", "Mu Booking")
        frappe.db.commit()
    
    from frappe.utils.fixtures import export_fixtures
    export_fixtures(app="mu_booking")
    print("Fixtures exported successfully!")
