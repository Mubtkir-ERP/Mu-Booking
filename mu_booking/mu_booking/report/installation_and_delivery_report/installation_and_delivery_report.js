frappe.query_reports["Installation and Delivery Report"] = {
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
            "default": frappe.datetime.get_today()
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nDraft\nConfirmed\nDelivery/Installation Scheduled\nExecuted\nPending Return\nClosed\nCancelled"
        }
    ]
};
