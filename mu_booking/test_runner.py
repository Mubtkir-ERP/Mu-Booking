# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe


@frappe.whitelist()
def fix_workspace():
	"""System Manager utility to refresh workspace links and report references."""
	frappe.only_for("System Manager")
	frappe.db.sql("UPDATE `tabReport` SET ref_doctype='Asset' WHERE name='Asset Utilization Report'")
	frappe.db.sql(
		"UPDATE `tabWorkspace Link` SET report_ref_doctype='Asset' WHERE link_to='Asset Utilization Report'"
	)
	frappe.db.sql(
		"UPDATE `tabWorkspace Shortcut` SET report_ref_doctype='Asset' WHERE link_to='Asset Utilization Report'"
	)
	frappe.db.commit()
	frappe.clear_cache()
	return {"status": "success", "message": "Workspace and report references refreshed."}
