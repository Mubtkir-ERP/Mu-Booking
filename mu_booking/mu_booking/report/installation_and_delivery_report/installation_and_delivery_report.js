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
            "fieldname": "workflow_state",
            "label": __("Status"),
            "fieldtype": "Link",
            "options": "Workflow State"
        }
    ]
};
