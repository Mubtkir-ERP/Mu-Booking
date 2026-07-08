import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "name", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 150},
        {"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "customer_mobile", "label": _("Customer Mobile"), "fieldtype": "Data", "width": 120},
        {"fieldname": "party_date", "label": _("Party Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "party_time", "label": _("Party Time"), "fieldtype": "Time", "width": 100},
        {"fieldname": "event_type", "label": _("Event Type"), "fieldtype": "Link", "options": "Event Type", "width": 120},
        {"fieldname": "service_type", "label": _("Service Type"), "fieldtype": "Data", "width": 150},
        {"fieldname": "booking_type", "label": _("Booking Type"), "fieldtype": "Data", "width": 120},
        {"fieldname": "workflow_state", "label": _("State"), "fieldtype": "Data", "width": 120}
    ]

def get_data(filters):
    conditions = ""
    values = {}
    
    if filters.get("from_date"):
        conditions += " AND party_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")
        
    if filters.get("to_date"):
        conditions += " AND party_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")
        
    if filters.get("workflow_state"):
        conditions += " AND workflow_state = %(workflow_state)s"
        values["workflow_state"] = filters.get("workflow_state")
        
    if filters.get("booking_type"):
        conditions += " AND booking_type = %(booking_type)s"
        values["booking_type"] = filters.get("booking_type")

    query = f"""
        SELECT 
            name, customer_name, customer_mobile, party_date, party_time,
            event_type, service_type, booking_type, workflow_state
        FROM `tabParty Booking`
        WHERE docstatus < 2 {conditions}
        ORDER BY party_date DESC
    """
    
    return frappe.db.sql(query, values, as_dict=True)
