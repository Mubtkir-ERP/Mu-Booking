// Copyright (c) 2026, Mu Booking and contributors
// For license information, please see license.txt

const STATUS_COLORS = {
	Draft: "red",
	Confirmed: "blue",
	"Delivery/Installation Scheduled": "orange",
	Executed: "purple",
	"Pending Return": "yellow",
	Closed: "green",
	Cancelled: "gray",
};

frappe.listview_settings["Party Booking"] = {
	add_fields: ["status", "deposit_status", "booking_type", "party_day", "party_location"],
	has_indicator_for_draft: 1,

	get_indicator(doc) {
		const status = doc.status || "Draft";
		return [__(status), STATUS_COLORS[status] || "blue", `status,=,${status}`];
	},

	onload(listview) {
		listview.page.add_inner_button(__("Order Tracking Kanban"), () => {
			frappe.set_route("List", "Party Booking", "Kanban", "Party Booking Status");
		});
	},
};
