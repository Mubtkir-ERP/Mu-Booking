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
		{"fieldname": "asset_name", "label": _("Asset Barcode"), "fieldtype": "Link", "options": "Asset", "width": 140},
		{"fieldname": "asset_title", "label": _("Asset Title"), "fieldtype": "Data", "width": 160},
		{"fieldname": "asset_value", "label": _("Asset Value"), "fieldtype": "Currency", "width": 120},
		{"fieldname": "booking_id", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 140},
		{"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
		{"fieldname": "sales_person", "label": _("Sales Person"), "fieldtype": "Link", "options": "Sales Person", "width": 140},
		{"fieldname": "party_date", "label": _("Party Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "return_doc", "label": _("Return Document"), "fieldtype": "Link", "options": "Party Asset Return", "width": 150},
		{"fieldname": "return_date", "label": _("Return Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "deduction_reason", "label": _("Damage/Loss Reason"), "fieldtype": "Data", "width": 220},
		{"fieldname": "deducted_amount", "label": _("Deducted Compensation"), "fieldtype": "Currency", "width": 150},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("from_date"):
		conditions += " AND COALESCE(r.refund_date, b.party_date) >= %(from_date)s"
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions += " AND COALESCE(r.refund_date, b.party_date) <= %(to_date)s"
		values["to_date"] = filters.get("to_date")

	if filters.get("sales_person"):
		conditions += " AND b.sales_person = %(sales_person)s"
		values["sales_person"] = filters.get("sales_person")

	query = f"""
		SELECT
			pba.asset_name AS asset_name,
			COALESCE(pba.asset_title, a.asset_name) AS asset_title,
			COALESCE(pba.asset_value, a.gross_purchase_amount, 0) AS asset_value,
			b.name AS booking_id,
			b.customer_name AS customer_name,
			b.sales_person AS sales_person,
			b.party_date AS party_date,
			r.name AS return_doc,
			r.refund_date AS return_date,
			r.deduction_reason AS deduction_reason,
			IFNULL(r.deduction_amount, 0) AS deducted_amount
		FROM `tabParty Booking Asset` pba
		INNER JOIN `tabParty Booking` b ON b.name = pba.parent
		LEFT JOIN `tabAsset` a ON a.name = pba.asset_name
		LEFT JOIN `tabParty Asset Return` r ON r.party_booking = b.name AND r.docstatus < 2
		WHERE b.docstatus < 2
		  AND (pba.asset_booking_status = 'Damaged' OR IFNULL(r.deduction_amount, 0) > 0)
		  {conditions}
		ORDER BY COALESCE(r.refund_date, b.party_date) DESC
	"""

	return frappe.db.sql(query, values, as_dict=True)
