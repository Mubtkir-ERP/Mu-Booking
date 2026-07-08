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
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "workflow_state",
            "label": __("State"),
            "fieldtype": "Link",
            "options": "Workflow State"
        },
        {
            "fieldname": "booking_type",
            "label": __("Booking Type"),
            "fieldtype": "Select",
            "options": "\nOne-time\nRecurring"
        }
    ]
};
