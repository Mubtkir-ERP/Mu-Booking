// Copyright (c) 2026, Mu Booking and contributors
// Make file/image uploads default to Public (uncheck "Private" by default)

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

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", patch_file_uploader);
	} else {
		patch_file_uploader();
	}
	$(document).on("app_ready", patch_file_uploader);
})();

