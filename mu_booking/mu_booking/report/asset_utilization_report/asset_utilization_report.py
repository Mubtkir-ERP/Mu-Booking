# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "asset_name", "label": _("Asset Barcode"), "fieldtype": "Link", "options": "Asset", "width": 150},
		{"fieldname": "asset_title", "label": _("Asset Title"), "fieldtype": "Data", "width": 160},
		{"fieldname": "item_code", "label": _("Item Code"), "fieldtype": "Link", "options": "Item", "width": 140},
		{"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 140},
		{"fieldname": "total_asset_qty", "label": _("Total Asset Qty"), "fieldtype": "Int", "width": 120},
		{"fieldname": "asset_value", "label": _("Asset Value"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_rentals", "label": _("Total Rentals"), "fieldtype": "Int", "width": 120},
		{"fieldname": "total_days", "label": _("Total Days Booked"), "fieldtype": "Int", "width": 140},
		{"fieldname": "current_status", "label": _("Current Status"), "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("item_group"):
		conditions += " AND i.item_group = %(item_group)s"
		values["item_group"] = filters.get("item_group")

	date_condition = ""
	if filters.get("from_date") and filters.get("to_date"):
		date_condition = " AND pb.party_date BETWEEN %(from_date)s AND %(to_date)s "
		values["from_date"] = filters.get("from_date")
		values["to_date"] = filters.get("to_date")

	query = f"""
		SELECT
			a.name AS asset_name,
			a.asset_name AS asset_title,
			a.item_code,
			i.item_group AS item_group,
			IFNULL(a.asset_quantity, 1) AS total_asset_qty,
			IFNULL(a.gross_purchase_amount, 0) AS asset_value,
			IFNULL(a.party_booking_status, 'Available') AS current_status,
			COUNT(DISTINCT pb.name) AS total_rentals,
			SUM(CASE WHEN pb.name IS NOT NULL THEN IFNULL(pb.number_of_days, 1) ELSE 0 END) AS total_days
		FROM `tabAsset` a
		LEFT JOIN `tabItem` i ON a.item_code = i.name
		LEFT JOIN `tabParty Booking Asset` pba ON pba.asset_name = a.name
		LEFT JOIN `tabParty Booking` pb ON pb.name = pba.parent AND pb.docstatus = 1 {date_condition}
		WHERE a.docstatus < 2 {conditions}
		GROUP BY a.name
		ORDER BY total_rentals DESC
	"""

	rows = frappe.db.sql(query, values, as_dict=True)
	for row in rows:
		if row.get("current_status"):
			row["current_status"] = _(row["current_status"])
	return rows
