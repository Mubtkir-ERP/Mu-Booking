// Copyright (c) 2026, Mu Booking and contributors
// For license information, please see license.txt

frappe.query_reports["Installation & Delivery Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("Delivery From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("Delivery To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), 3)
		},
		{
			"fieldname": "installation_manager",
			"label": __("Installation Manager"),
			"fieldtype": "Link",
			"options": "Employee"
		},
		{
			"fieldname": "pickup_status",
			"label": __("Asset Pickup Status"),
			"fieldtype": "Select",
			"options": "\nNot Picked Up\nPicked Up"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nConfirmed\nDelivery/Installation Scheduled\nExecuted\nPending Return\nClosed\nCancelled"
		}
	]
};
