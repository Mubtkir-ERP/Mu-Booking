import frappe

def execute():
    frappe.reload_doc('mu_booking', 'doctype', 'party_booking', force=True)
