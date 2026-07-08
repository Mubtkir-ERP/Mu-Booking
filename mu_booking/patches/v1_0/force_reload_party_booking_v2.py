import frappe

def execute():
    # Force custom=0 so frappe allows overwriting it from JSON
    frappe.db.set_value('DocType', 'Party Booking', 'custom', 0)
    frappe.db.commit()
    # Now reload the JSON schema forcibly
    frappe.reload_doc('mu_booking', 'doctype', 'party_booking', force=True)
    # Clear cache
    frappe.clear_cache(doctype='Party Booking')
