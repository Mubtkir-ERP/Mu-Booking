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
		{"fieldname": "booking_id", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 150},
		{"fieldname": "name", "label": _("Return Document"), "fieldtype": "Link", "options": "Party Asset Return", "width": 160},
		{"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
		{"fieldname": "refund_date", "label": _("Return Date"), "fieldtype": "Date", "width": 120},
		{"fieldname": "original_deposit", "label": _("Deposit Amount"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "refund_amount", "label": _("Returned Amount"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "deduction_amount", "label": _("Deducted Amount"), "fieldtype": "Currency", "width": 130},
		{"fieldname": "deduction_reason", "label": _("Deduction Reason"), "fieldtype": "Data", "width": 200},
		{"fieldname": "refund_status", "label": _("Return Status"), "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("from_date"):
		conditions += " AND r.refund_date >= %(from_date)s"
		values["from_date"] = filters.get("from_date")

	if filters.get("to_date"):
		conditions += " AND r.refund_date <= %(to_date)s"
		values["to_date"] = filters.get("to_date")

	query = f"""
		SELECT
			r.party_booking AS booking_id,
			r.name,
			b.customer_name,
			r.refund_date,
			r.original_deposit,
			r.refund_amount,
			r.deduction_amount,
			r.deduction_reason,
			r.refund_status
		FROM `tabParty Asset Return` r
		LEFT JOIN `tabParty Booking` b ON b.name = r.party_booking
		WHERE r.docstatus < 2 {conditions}
		ORDER BY r.refund_date DESC
	"""

	rows = frappe.db.sql(query, values, as_dict=True)
	for row in rows:
		if row.get("refund_status"):
			row["refund_status"] = _(row["refund_status"])
	return rows
