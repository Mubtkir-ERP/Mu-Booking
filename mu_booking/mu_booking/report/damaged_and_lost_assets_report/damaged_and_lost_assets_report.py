import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "asset_name", "label": _("Asset"), "fieldtype": "Link", "options": "Asset", "width": 150},
        {"fieldname": "return_doc", "label": _("Return Document"), "fieldtype": "Link", "options": "Party Asset Return", "width": 160},
        {"fieldname": "booking_id", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 150},
        {"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
        {"fieldname": "return_date", "label": _("Return Date"), "fieldtype": "Date", "width": 120},
        {"fieldname": "deduction_reason", "label": _("Damage/Loss Reason"), "fieldtype": "Data", "width": 250},
        {"fieldname": "deducted_amount", "label": _("Deducted Compensation"), "fieldtype": "Currency", "width": 150}
    ]

def get_data(filters):
    conditions = ""
    values = {}
    
    if filters.get("from_date"):
        conditions += " AND r.return_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")
        
    if filters.get("to_date"):
        conditions += " AND r.return_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    query = f"""
        SELECT 
            r.name as return_doc,
            r.party_booking as booking_id,
            b.customer_name,
            r.return_date,
            r.deduction_reason,
            r.deducted_amount,
            ra.asset as asset_name
        FROM `tabParty Asset Return` r
        LEFT JOIN `tabParty Booking` b ON b.name = r.party_booking
        JOIN `tabParty Returned Asset` ra ON ra.parent = r.name
        WHERE r.docstatus = 1 AND r.deducted_amount > 0 {conditions}
        ORDER BY r.return_date DESC
    """
    
    return frappe.db.sql(query, values, as_dict=True)
