// Copyright (c) 2026, Mu Booking and contributors
// For license information, please see license.txt

const AVAILABLE_ASSET_FILTERS = [["party_booking_status", "not in", ["Damaged", "Lost"]]];

frappe.ui.form.on("Party Booking", {
	setup(frm) {
		frm.set_query("asset_name", "assets", () => ({ filters: AVAILABLE_ASSET_FILTERS }));
		frm.set_query("alternative_asset", "sessions", () => ({ filters: AVAILABLE_ASSET_FILTERS }));
	},

	onload(frm) {
		// Open new bookings with one empty asset row ready to fill
		if (frm.is_new() && !(frm.doc.assets || []).length) {
			frm.add_child("assets");
			frm.refresh_field("assets");
		}
	},

	refresh(frm) {
		render_action_buttons(frm);
		render_asset_gallery(frm);
	},

	open_map(frm) {
		if (frm.doc.location_link) {
			window.open(frm.doc.location_link, "_blank");
		}
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
		// Frappe may rebuild the grid row when the fetched asset fields arrive,
		// which can make it scroll the page back to the top - keep the position
		guard_scroll_position();
		render_asset_gallery(frm);
		warn_if_asset_unavailable(frm, locals[cdt][cdn].asset_name);
	},
	assets_add(frm) {
		guard_scroll_position();
	},
	assets_remove(frm) {
		render_asset_gallery(frm);
	},
});

frappe.ui.form.on("Party Booking Session", {
	alternative_asset(frm, cdt, cdn) {
		warn_if_asset_unavailable(frm, locals[cdt][cdn].alternative_asset);
	},
});

// Warn the moment an asset is picked if it is still held by an active booking
function warn_if_asset_unavailable(frm, asset) {
	if (!asset) {
		return;
	}
	frappe.xcall(
		"mu_booking.mu_booking.doctype.party_booking.party_booking.get_asset_holding_booking",
		{ asset, exclude_booking: frm.doc.name }
	).then((holding_booking) => {
		if (holding_booking) {
			frappe.msgprint({
				title: __("Asset Not Available"),
				indicator: "orange",
				message: __(
					"Asset <b>{0}</b> is held by active Booking {1} and has not been returned yet",
					[asset, `<a href="/app/party-booking/${encodeURIComponent(holding_booking)}">${holding_booking}</a>`]
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
			add_styled_button(frm, __("Create Asset Return"), () => {
				frappe.new_doc("Party Asset Return", { party_booking: frm.doc.name });
			}, "btn-primary");
		}

		if (r.can_cancel) {
			add_styled_button(frm, __("Cancel Booking"), () => {
				frappe.confirm(__("Are you sure you want to cancel this booking?"), () => frm.savecancel());
			}, "btn-danger");
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
	const asset_names = [...new Set((frm.doc.assets || []).map((row) => row.asset_name).filter(Boolean))].sort();

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
			fields: ["name", "asset_name", "image", "gross_purchase_amount"],
		})
		.then((assets) => wrapper.html(build_gallery_html(assets)));
}

function build_gallery_html(assets) {
	const cards = assets
		.map((asset) => {
			const title = frappe.utils.escape_html(asset.asset_name || asset.name);
			const image = asset.image
				? `<img src="${encodeURI(asset.image)}" alt="${title}" style="width:100%;height:120px;object-fit:cover;">`
				: `<div style="width:100%;height:120px;display:flex;align-items:center;justify-content:center;color:var(--text-muted);">${frappe.utils.icon("image", "lg")}</div>`;
			return `
				<div style="width:160px;border:1px solid var(--border-color);border-radius:var(--border-radius-md);overflow:hidden;background:var(--card-bg);">
					${image}
					<div style="padding:8px;">
						<div class="ellipsis" style="font-weight:600;" title="${title}">${title}</div>
						<div class="text-muted small">${frappe.utils.escape_html(asset.name)}</div>
						<div class="small">${format_currency(asset.gross_purchase_amount)}</div>
					</div>
				</div>`;
		})
		.join("");

	return `<div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:8px;">${cards}</div>`;
}
