// Copyright (c) 2026, Mu Booking and contributors
// For license information, please see license.txt

frappe.ui.form.on("Party Asset Return", {
	onload(frm) {
		if (frm.meta) {
			frm.meta.make_attachments_public = 1;
		}
	},
	refresh(frm) {
		if (frm.meta) {
			frm.meta.make_attachments_public = 1;
		}
	},
	refund_amount(frm) {
		const original = Number(frm.doc.original_deposit || 0);
		const refund = Number(frm.doc.refund_amount || 0);
		frm.set_value("deduction_amount", Math.max(original - refund, 0));
	},
});
