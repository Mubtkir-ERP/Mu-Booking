import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "booking_id", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 150},
        {"fieldname": "name", "label": _("Return Document"), "fieldtype": "Link", "options": "Party Asset Return", "width": 160},
        {"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "return_date", "label": _("Return Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "security_deposit_amount", "label": _("Deposit Amount"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "returned_amount", "label": _("Returned Amount"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "deducted_amount", "label": _("Deducted Amount"), "fieldtype": "Currency", "width": 130},
        {"fieldname": "deduction_reason", "label": _("Deduction Reason"), "fieldtype": "Data", "width": 200},
        {"fieldname": "workflow_state", "label": _("Return Status"), "fieldtype": "Data", "width": 120}
    ]

def get_data(filters):
    conditions = ""
    values = {}
    
    if filters.get("from_date"):
        conditions += " AND return_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")
        
    if filters.get("to_date"):
        conditions += " AND return_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    query = f"""
        SELECT 
            r.party_booking as booking_id,
            r.name,
            b.customer_name,
            r.return_date,
            r.security_deposit_amount,
            r.returned_amount,
            r.deducted_amount,
            r.deduction_reason,
            r.workflow_state
        FROM `tabParty Asset Return` r
        LEFT JOIN `tabParty Booking` b ON b.name = r.party_booking
        WHERE r.docstatus < 2 {conditions}
        ORDER BY r.return_date DESC
    """
    
    return frappe.db.sql(query, values, as_dict=True)
