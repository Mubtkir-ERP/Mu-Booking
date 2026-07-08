import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "asset_name", "label": _("Asset"), "fieldtype": "Link", "options": "Asset", "width": 150},
        {"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 150},
        {"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 150},
        {"fieldname": "total_rentals", "label": _("Total Rentals"), "fieldtype": "Int", "width": 120},
        {"fieldname": "total_days", "label": _("Total Days Booked"), "fieldtype": "Int", "width": 150},
        {"fieldname": "current_status", "label": _("Current Status"), "fieldtype": "Data", "width": 120}
    ]

def get_data(filters):
    conditions = ""
    values = {}
    
    if filters.get("item_group"):
        conditions += " AND a.item_group = %(item_group)s"
        values["item_group"] = filters.get("item_group")
        
    date_condition = ""
    if filters.get("from_date") and filters.get("to_date"):
        date_condition = " AND pb.party_date BETWEEN %(from_date)s AND %(to_date)s "
        values["from_date"] = filters.get("from_date")
        values["to_date"] = filters.get("to_date")

    query = f"""
        SELECT 
            a.name as asset_name,
            a.item_code,
            a.item_group,
            a.party_booking_status as current_status,
            COUNT(DISTINCT pb.name) as total_rentals,
            SUM(IFNULL(pb.number_of_days, 1)) as total_days
        FROM `tabAsset` a
        LEFT JOIN `tabParty Booking Asset` pba ON pba.asset_name = a.name
        LEFT JOIN `tabParty Booking` pb ON pb.name = pba.parent AND pb.docstatus = 1 {date_condition}
        WHERE a.is_existing_asset = 1 {conditions}
        GROUP BY a.name
        ORDER BY total_rentals DESC
    """
    
    return frappe.db.sql(query, values, as_dict=True)
