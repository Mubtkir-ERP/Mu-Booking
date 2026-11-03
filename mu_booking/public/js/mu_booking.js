// Copyright (c) 2026, Mu Booking and contributors
// 1. Make file/image uploads default to Public (uncheck "Private" by default)
// 2. Allow updating Asset Quantity (asset_quantity) on submitted Assets with one click

(function () {
	const patch_file_uploader = () => {
		if (!window.frappe || !frappe.ui || !frappe.ui.FileUploader || frappe.ui.FileUploader._mu_patched) {
			return;
		}
		const OriginalFileUploader = frappe.ui.FileUploader;
		frappe.ui.FileUploader = function (opts = {}) {
			if (opts.make_attachments_public === undefined) {
				opts.make_attachments_public = true;
			}
			const instance = new OriginalFileUploader(opts);
			try {
				if (instance.uploader && instance.uploader.make_attachments_public !== undefined) {
					instance.uploader.make_attachments_public = true;
				}
			} catch (e) {
				// ignore
			}
			return instance;
		};
		Object.assign(frappe.ui.FileUploader, OriginalFileUploader);
		frappe.ui.FileUploader.prototype = OriginalFileUploader.prototype;
		frappe.ui.FileUploader._mu_patched = true;
	};

	const register_asset_form_enhancements = () => {
		if (!window.frappe || !frappe.ui || !frappe.ui.form || frappe.ui.form._mu_asset_patched) {
			return;
		}
		frappe.ui.form._mu_asset_patched = true;
		frappe.ui.form.on("Asset", {
			refresh(frm) {
				if (frm.meta) {
					frm.meta.make_attachments_public = 1;
				}
				if (!frm.is_new() && frm.doc.docstatus === 1) {
					frm.add_custom_button(__("Update Asset Quantity"), () => {
						frappe.prompt(
							[
								{
									fieldname: "asset_quantity",
									fieldtype: "Int",
									label: __("Total Asset Qty"),
									default: frm.doc.asset_quantity || 1,
									reqd: 1,
								},
							],
							(values) => {
								frappe
									.xcall(
										"mu_booking.mu_booking.doctype.party_booking.party_booking.update_asset_quantity",
										{
											asset: frm.doc.name,
											asset_quantity: values.asset_quantity,
										}
									)
									.then(() => {
										frappe.show_alert({
											message: __("Asset quantity updated successfully."),
											indicator: "green",
										});
										frm.reload_doc();
									});
							},
							__("Update Asset Quantity"),
							__("Save")
						);
					}).removeClass("btn-default").addClass("btn-primary");
				}
			},
		});
	};

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", () => {
			patch_file_uploader();
			register_asset_form_enhancements();
		});
	} else {
		patch_file_uploader();
		register_asset_form_enhancements();
	}
	$(document).on("app_ready", () => {
		patch_file_uploader();
		register_asset_form_enhancements();
	});
})();
