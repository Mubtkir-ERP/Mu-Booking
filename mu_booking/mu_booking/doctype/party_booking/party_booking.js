// Copyright (c) 2026, Mu Booking and contributors
// For license information, please see license.txt

const AVAILABLE_ASSET_FILTERS = [["party_booking_status", "not in", ["Damaged", "Lost"]]];
const JS_WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

// Default file uploader to public (unchecked Private checkbox) on Party Booking & Asset
$(document).on("NodeInserted DOMNodeInserted", () => {
	// Ensure any open FileUploader dialog on booking/asset screens defaults to public
});

frappe.ui.form.on("Party Booking", {
	setup(frm) {
		frm.set_query("asset_name", "assets", () => ({ filters: AVAILABLE_ASSET_FILTERS }));
		frm.set_query("alternative_asset", "sessions", () => ({ filters: AVAILABLE_ASSET_FILTERS }));
	},

	onload(frm) {
		// Ensure attachments uploaded from this form default to public (no lock)
		if (frm.meta) {
			frm.meta.make_attachments_public = 1;
		}
		// Open new bookings with one empty asset row ready to fill
		if (frm.is_new() && !(frm.doc.assets || []).length) {
			frm.add_child("assets");
			frm.refresh_field("assets");
		}
		if (frm.doc.party_date && !frm.doc.party_day) {
			update_party_day(frm);
		}
	},

	refresh(frm) {
		if (frm.meta) {
			frm.meta.make_attachments_public = 1;
		}
		render_action_buttons(frm);
		render_asset_gallery(frm);
		refresh_all_assets_availability(frm);
	},

	open_map(frm) {
		if (frm.doc.location_link) {
			const url = (frm.doc.location_link || "").trim();
			if (/^https?:\/\//i.test(url)) {
				window.open(url, "_blank", "noopener,noreferrer");
			} else {
				frappe.msgprint(__("Invalid map URL. Must start with http:// or https://"));
			}
		}
	},

	party_date(frm) {
		update_party_day(frm);
		refresh_all_assets_availability(frm);
	},

	start_date(frm) {
		calculate_daily_end_date(frm);
	},

	number_of_days(frm) {
		calculate_daily_end_date(frm);
	},
});

frappe.ui.form.on("Party Booking Asset", {
	asset_name(frm, cdt, cdn) {
		guard_scroll_position();
		const row = locals[cdt][cdn];
		render_asset_gallery(frm);
		update_and_check_asset_row(frm, row, true);
	},
	qty(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		update_and_check_asset_row(frm, row, true);
	},
	assets_add(frm) {
		guard_scroll_position();
	},
	assets_remove(frm) {
		render_asset_gallery(frm);
	},
});

frappe.ui.form.on("Party Booking Session", {
	session_date(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.session_date) {
			frappe.model.set_value(cdt, cdn, "session_day", get_weekday_label(row.session_date));
		}
	},
	alternative_asset(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (row.alternative_asset) {
			check_alternative_asset_availability(frm, row);
		}
	},
});

function get_weekday_label(date_str) {
	if (!date_str) {
		return "";
	}
	const parts = date_str.split("-");
	if (parts.length !== 3) {
		return "";
	}
	const dt = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
	if (isNaN(dt.getTime())) {
		return "";
	}
	return __(JS_WEEKDAYS[dt.getDay()]);
}

function update_party_day(frm) {
	const day_label = get_weekday_label(frm.doc.party_date);
	if (frm.doc.party_day !== day_label) {
		frm.set_value("party_day", day_label);
	}
}

function refresh_all_assets_availability(frm) {
	(frm.doc.assets || []).forEach((row) => {
		if (row.asset_name) {
			update_and_check_asset_row(frm, row, false);
		}
	});
}

function update_and_check_asset_row(frm, row, show_messages) {
	if (!row || !row.asset_name) {
		return;
	}
	frappe.xcall(
		"mu_booking.mu_booking.doctype.party_booking.party_booking.get_asset_availability_info",
		{
			asset: row.asset_name,
			party_date: frm.doc.party_date,
			exclude_booking: frm.doc.name,
		}
	).then((info) => {
		if (!info || !info.asset) {
			return;
		}
		frappe.model.set_value(row.doctype, row.name, "total_asset_qty", info.total_asset_qty || 1);
		frappe.model.set_value(row.doctype, row.name, "available_qty", info.available_qty ?? 1);
		if (!row.asset_value && info.asset_value) {
			frappe.model.set_value(row.doctype, row.name, "asset_value", info.asset_value);
		}

		if (!show_messages) {
			return;
		}

		const req_qty = Number(row.qty || 1);
		const avail_qty = Number(info.available_qty ?? 1);
		const total_qty = Number(info.total_asset_qty || 1);
		const safe_asset = frappe.utils.escape_html(row.asset_name);

		if (frm.doc.party_date && req_qty > avail_qty) {
			const holders = (info.holding_bookings || [])
				.map(
					(b) =>
						`<a href="/app/party-booking/${encodeURIComponent(b)}">${frappe.utils.escape_html(b)}</a>`
				)
				.join(", ");
			frappe.msgprint({
				title: __("Asset Not Available"),
				indicator: "orange",
				message: __(
					"Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2} (Requested: {3}, Available: {4} of {5})",
					[
						safe_asset,
						frappe.utils.escape_html(frm.doc.party_date),
						holders || "-",
						req_qty,
						avail_qty,
						total_qty,
					]
				),
			});
		} else if (info.upcoming_bookings && info.upcoming_bookings.length) {
			const other_dates = info.upcoming_bookings
				.filter((u) => u.party_date !== frm.doc.party_date)
				.map((u) => `${frappe.utils.escape_html(u.party_date)} (${frappe.utils.escape_html(u.name)})`)
				.join("، ");
			if (other_dates) {
				frappe.show_alert(
					{
						message: __(
							"Asset <b>{0}</b> is available on this date (Available: {1} of {2}). Scheduled on other dates: {3}",
							[safe_asset, avail_qty, total_qty, other_dates]
						),
						indicator: "blue",
					},
					7
				);
			}
		}
	});
}

function check_alternative_asset_availability(frm, row) {
	if (!row.alternative_asset) {
		return;
	}
	frappe.xcall(
		"mu_booking.mu_booking.doctype.party_booking.party_booking.get_asset_availability_info",
		{
			asset: row.alternative_asset,
			party_date: row.session_date || frm.doc.party_date,
			exclude_booking: frm.doc.name,
		}
	).then((info) => {
		if (info && info.available_qty < 1 && info.holding_booking) {
			const safe_asset = frappe.utils.escape_html(row.alternative_asset);
			const safe_booking = frappe.utils.escape_html(info.holding_booking);
			frappe.msgprint({
				title: __("Asset Not Available"),
				indicator: "orange",
				message: __(
					"Asset <b>{0}</b> is already booked on <b>{1}</b> in Booking {2}",
					[
						safe_asset,
						frappe.utils.escape_html(row.session_date || frm.doc.party_date || ""),
						`<a href="/app/party-booking/${encodeURIComponent(info.holding_booking)}">${safe_booking}</a>`,
					]
				),
			});
		}
	});
}

function guard_scroll_position() {
	const scroller = document.scrollingElement;
	const y = scroller.scrollTop;
	if (y < 200) {
		return;
	}
	const restore = () => {
		if (scroller.scrollTop < y - 200) {
			$("html, body").stop(true);
			scroller.scrollTop = y;
		}
	};
	[100, 300, 600].forEach((delay) => setTimeout(restore, delay));
}

function calculate_daily_end_date(frm) {
	if (frm.doc.recurring_pattern === "Daily" && frm.doc.start_date && frm.doc.number_of_days > 0) {
		frm.set_value("end_date", frappe.datetime.add_days(frm.doc.start_date, frm.doc.number_of_days - 1));
	}
}

// ---------------------------------------------------------------------------
// Lifecycle buttons (replaces the Workflow "Actions" dropdown)
// ---------------------------------------------------------------------------

function render_action_buttons(frm) {
	frm.clear_custom_buttons();
	if (frm.is_new() || frm.is_dirty()) {
		return;
	}

	frappe.xcall("mu_booking.mu_booking.doctype.party_booking.party_booking.get_allowed_actions", {
		name: frm.doc.name,
	}).then((r) => {
		if (frm.is_dirty()) {
			return; // the user started editing meanwhile - keep the Save button
		}
		// Replace Frappe's default Submit (primary) and Cancel (secondary) actions
		// with role-specific buttons
		frm.page.clear_secondary_action();
		if (r.can_confirm) {
			frm.page.set_primary_action(__("Confirm Booking"), () => frm.savesubmit());
		} else {
			frm.page.clear_primary_action();
		}

		r.actions.forEach((action) => {
			add_styled_button(frm, action.label, () => run_action(frm, action), "btn-primary");
		});

		if (r.can_create_return) {
			add_styled_button(
				frm,
				__("Create Asset Return"),
				() => {
					frappe.new_doc("Party Asset Return", { party_booking: frm.doc.name });
				},
				"btn-primary"
			);
		}

		if (r.can_cancel) {
			add_styled_button(
				frm,
				__("Cancel Booking"),
				() => {
					frappe.confirm(__("Are you sure you want to cancel this booking?"), () =>
						frm.savecancel()
					);
				},
				"btn-danger"
			);
		}
	});
}

// Custom buttons come with `btn-default`, which overrides the colored variants
function add_styled_button(frm, label, handler, css_class) {
	return frm.add_custom_button(label, handler).removeClass("btn-default").addClass(css_class);
}

function run_action(frm, action) {
	if (action.requires_installation_manager) {
		prompt_installation_manager(frm, (installation_manager) =>
			apply_action(frm, action.action, { installation_manager })
		);
	} else {
		apply_action(frm, action.action);
	}
}

function prompt_installation_manager(frm, callback) {
	const dialog = new frappe.ui.Dialog({
		title: __("Select Installation Manager"),
		fields: [
			{
				fieldname: "installation_manager",
				fieldtype: "Link",
				label: __("Installation Manager"),
				options: "Employee",
				reqd: 1,
				default: frm.doc.installation_manager,
				get_query: () => ({ filters: { status: "Active" } }),
			},
		],
		primary_action_label: __("Schedule"),
		primary_action(values) {
			dialog.hide();
			callback(values.installation_manager);
		},
	});
	dialog.show();
}

function apply_action(frm, action, extra_args = {}) {
	frappe.xcall("mu_booking.mu_booking.doctype.party_booking.party_booking.apply_action", {
		name: frm.doc.name,
		action,
		...extra_args,
	}).then(() => frm.reload_doc());
}

// ---------------------------------------------------------------------------
// Asset gallery rendered below the assets table
// ---------------------------------------------------------------------------

function render_asset_gallery(frm) {
	const wrapper = frm.get_field("assets_gallery").$wrapper;
	const asset_names = [
		...new Set((frm.doc.assets || []).map((row) => row.asset_name).filter(Boolean)),
	].sort();

	// Skip when nothing changed (refresh calls this too)
	const key = asset_names.join("|");
	if (frm._assets_gallery_key === key) {
		return;
	}
	frm._assets_gallery_key = key;

	if (!asset_names.length) {
		wrapper.empty();
		return;
	}

	frappe.db
		.get_list("Asset", {
			filters: { name: ["in", asset_names] },
			fields: ["name", "asset_name", "image", "gross_purchase_amount", "asset_quantity"],
		})
		.then((assets) => wrapper.html(build_gallery_html(assets)));
}

function build_gallery_html(assets) {
	const cards = assets
		.map((asset) => {
			const title = frappe.utils.escape_html(asset.asset_name || asset.name);
			const barcode = frappe.utils.escape_html(asset.name);
			const total_qty = Number(asset.asset_quantity || 1);
			const image = asset.image
				? `<img src="${encodeURI(asset.image)}" alt="${title}" style="width:100%;height:120px;object-fit:cover;">`
				: `<div style="width:100%;height:120px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);">${frappe.utils.icon("image", "lg")}</div>`;
			return `
				<div style="width:180px;border:1px solid var(--border-color);border-radius:var(--border-radius-md);overflow:hidden;background:var(--card-bg);">
					${image}
					<div style="padding:8px;">
						<div class="ellipsis" style="font-weight:600;" title="${title}">${title}</div>
						<div class="text-muted small">${__("Asset Barcode")}: <b>${barcode}</b></div>
						<div class="small">${__("Asset Value")}: ${format_currency(asset.gross_purchase_amount)}</div>
						<div class="text-muted small">${__("Total Asset Qty")}: ${total_qty}</div>
					</div>
				</div>`;
		})
		.join("");

	return `<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;">${cards}</div>`;
}
