frappe.query_reports["Party Bookings Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1)
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), 3)
		},
		{
			"fieldname": "sales_person",
			"label": __("Sales Person"),
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname": "status",
			"label": __("Status"),
			"fieldtype": "Select",
			"options": "\nDraft\nConfirmed\nDelivery/Installation Scheduled\nExecuted\nPending Return\nClosed\nCancelled"
		},
		{
			"fieldname": "booking_type",
			"label": __("Booking Type"),
			"fieldtype": "Select",
			"options": "\nOne-time\nRecurring"
		}
	]
};
