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
		{"fieldname": "name", "label": _("Booking ID"), "fieldtype": "Link", "options": "Party Booking", "width": 140},
		{"fieldname": "customer_name", "label": _("Customer Name"), "fieldtype": "Data", "width": 150},
		{"fieldname": "customer_mobile", "label": _("Customer Mobile"), "fieldtype": "Data", "width": 120},
		{"fieldname": "sales_person", "label": _("Sales Person"), "fieldtype": "Link", "options": "Sales Person", "width": 140},
		{"fieldname": "party_date", "label": _("Party Date"), "fieldtype": "Date", "width": 110},
		{"fieldname": "party_day", "label": _("Day"), "fieldtype": "Data", "width": 95},
		{"fieldname": "party_time", "label": _("Party Time"), "fieldtype": "Time", "width": 100},
		{"fieldname": "party_location", "label": _("Party Location"), "fieldtype": "Data", "width": 140},
		{"fieldname": "installation_address", "label": _("Installation Address"), "fieldtype": "Data", "width": 160},
		{"fieldname": "event_type", "label": _("Event Type"), "fieldtype": "Link", "options": "Event Type", "width": 120},
		{"fieldname": "service_type", "label": _("Service Type"), "fieldtype": "Data", "width": 140},
		{"fieldname": "booking_type", "label": _("Booking Type"), "fieldtype": "Data", "width": 110},
		{"fieldname": "installation_manager_name", "label": _("Installation Manager Name"), "fieldtype": "Data", "width": 150},
		{"fieldname": "pickup_status", "label": _("Asset Pickup Status"), "fieldtype": "Data", "width": 130},
		{"fieldname": "warehouse_return_status", "label": _("Warehouse Return Status"), "fieldtype": "Data", "width": 140},
		{"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 130},
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

	if filters.get("status"):
		conditions += " AND status = %(status)s"
		values["status"] = filters.get("status")

	if filters.get("booking_type"):
		conditions += " AND booking_type = %(booking_type)s"
		values["booking_type"] = filters.get("booking_type")

	if filters.get("sales_person"):
		conditions += " AND sales_person = %(sales_person)s"
		values["sales_person"] = filters.get("sales_person")

	query = f"""
		SELECT
			name,
			customer_name,
			customer_mobile,
			sales_person,
			party_date,
			party_day,
			party_time,
			party_location,
			installation_address,
			event_type,
			service_type,
			booking_type,
			installation_manager_name,
			pickup_status,
			warehouse_return_status,
			status
		FROM `tabParty Booking`
		WHERE docstatus < 2 {conditions}
		ORDER BY party_date DESC
	"""

	rows = frappe.db.sql(query, values, as_dict=True)
	for row in rows:
		if row.get("party_day"):
			row["party_day"] = _(row["party_day"])
		if row.get("service_type"):
			row["service_type"] = _(row["service_type"])
		if row.get("booking_type"):
			row["booking_type"] = _(row["booking_type"])
		if row.get("pickup_status"):
			row["pickup_status"] = _(row["pickup_status"])
		if row.get("warehouse_return_status"):
			row["warehouse_return_status"] = _(row["warehouse_return_status"])
		if row.get("status"):
			row["status"] = _(row["status"])
	return rows
