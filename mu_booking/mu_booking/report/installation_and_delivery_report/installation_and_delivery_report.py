import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "name", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 150},
        {"fieldname": "location", "label": _("Location"), "fieldtype": "Data", "width": 180},
        {"fieldname": "party_date", "label": _("Party Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "delivery_time", "label": _("Delivery Time"), "fieldtype": "Time", "width": 120},
        {"fieldname": "execution_duration", "label": _("Duration"), "fieldtype": "Data", "width": 100},
        {"fieldname": "number_of_workers", "label": _("Workers"), "fieldtype": "Int", "width": 90},
        {"fieldname": "delivery_vehicle", "label": _("Vehicle"), "fieldtype": "Data", "width": 120},
        {"fieldname": "installation_team", "label": _("Installation Team"), "fieldtype": "Data", "width": 200},
        {"fieldname": "workflow_state", "label": _("Status"), "fieldtype": "Data", "width": 120}
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

    query = f"""
        SELECT 
            name, location, party_date, delivery_time, execution_duration,
            number_of_workers, delivery_vehicle, installation_team, workflow_state
        FROM `tabParty Booking`
        WHERE docstatus = 1 {conditions}
        ORDER BY party_date ASC, delivery_time ASC
    """
    
    return frappe.db.sql(query, values, as_dict=True)
