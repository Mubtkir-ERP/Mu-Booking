frappe.listview_settings['Party Booking'] = {
	add_fields: ["deposit_status", "booking_type", "workflow_state"],
	
	// This colors the main left-most 'Status' column (which is overridden by Workflow if active)
	get_indicator: function(doc) {
		// Handle Workflow States if Workflow is active
		if (doc.workflow_state) {
			let state = doc.workflow_state;
			if (state === "Draft") {
				return [__(state), "red", "workflow_state,=," + state];
			} else if (state === "Closed" || state === "Completed" || state === "Approved") {
				return [__(state), "green", "workflow_state,=," + state];
			} else if (state === "Pending" || state === "Review") {
				return [__(state), "orange", "workflow_state,=," + state];
			} else if (state === "Cancelled" || state === "Rejected") {
				return [__(state), "gray", "workflow_state,=," + state];
			}
			return [__(state), "blue", "workflow_state,=," + state];
		}

		// Standard Logic if no Workflow is active
		if (doc.docstatus === 0) {
			return [__("Draft"), "red", "docstatus,=,0"];
		} else if (doc.docstatus === 2) {
			return [__("Cancelled"), "gray", "docstatus,=,2"];
		} else if (doc.docstatus === 1) {
			if (doc.deposit_status === "Refunded") {
				return [__("Completed"), "green", "docstatus,=,1"];
			} else if (doc.deposit_status === "Partially Deducted") {
				return [__("Deducted"), "purple", "docstatus,=,1"];
			} else if (doc.deposit_status === "Pending") {
				return [__("Pending"), "orange", "docstatus,=,1"];
			} else {
				return [__("Submitted"), "blue", "docstatus,=,1"];
			}
		}
	},

	// This colors the actual text of 'Deposit Status' column if displayed
	formatters: {
		deposit_status: function(value, df, doc) {
			if (value === "Refunded") {
				return "<span class='indicator-pill green'>" + value + "</span>";
			} else if (value === "Partially Deducted") {
				return "<span class='indicator-pill purple'>" + value + "</span>";
			} else if (value === "Pending") {
				return "<span class='indicator-pill orange'>" + value + "</span>";
			}
			return value;
		}
	}
};
