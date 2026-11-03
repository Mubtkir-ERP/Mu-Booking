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
		render_pickup_and_employee_banner(frm);
		render_action_buttons(frm);
		render_asset_gallery(frm);
		render_employee_guide(frm);
		refresh_all_assets_availability(frm);
	},

	installation_manager(frm) {
		if (frm.doc.installation_manager) {
			frappe.xcall("mu_booking.mu_booking.doctype.party_booking.party_booking.get_employee_details", {
				employee: frm.doc.installation_manager,
			}).then((emp) => {
				if (emp) {
					frm.set_value("installation_manager_name", emp.employee_name || "");
					frm.set_value("installation_manager_mobile", emp.cell_number || "");
				}
			});
		} else {
			frm.set_value("installation_manager_name", "");
			frm.set_value("installation_manager_mobile", "");
		}
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
// Employee, Pickup & Warehouse Return Banner (Points 2, 3, 4, 15, 17)
// ---------------------------------------------------------------------------

function render_pickup_and_employee_banner(frm) {
	if (frm.is_new()) {
		frm.dashboard.set_headline_alert("");
		return;
	}

	const picked = frm.doc.pickup_status === "Picked Up";
	const pickup_badge = picked
		? `<span class="indicator-pill green">${__("Picked Up")}</span>`
		: `<span class="indicator-pill orange">${__("Not Picked Up")}</span>`;

	const arrival_info = frm.doc.pickup_arrival_time
		? `<span class="text-muted small" style="margin-inline-start:6px;">(${frappe.datetime.str_to_user(frm.doc.pickup_arrival_time)}${frm.doc.picked_up_by ? " - " + frappe.utils.escape_html(frm.doc.picked_up_by) : ""})</span>`
		: "";

	const emp_name = frappe.utils.escape_html(
		frm.doc.installation_manager_name || frm.doc.installation_manager || __("Not Assigned")
	);
	const emp_mobile = (frm.doc.installation_manager_mobile || "").trim();
	const emp_mobile_html = emp_mobile
		? ` <a href="tel:${encodeURIComponent(emp_mobile)}" style="font-weight:600;text-decoration:underline;">(${frappe.utils.escape_html(emp_mobile)})</a>`
		: "";

	const wh_returned = frm.doc.warehouse_return_status === "Returned to Warehouse";
	const wh_badge = wh_returned
		? `<span class="indicator-pill green">${__("Returned to Warehouse")}</span>`
		: `<span class="indicator-pill gray">${__("Not Returned")}</span>`;

	const html = `
		<div style="display:flex;flex-wrap:wrap;gap:16px;align-items:center;padding:4px 0;">
			<div><b>${__("Installation Manager")}:</b> ${emp_name}${emp_mobile_html}</div>
			<div><b>${__("Asset Pickup Status")}:</b> ${pickup_badge}${arrival_info}</div>
			<div><b>${__("Warehouse Return Status")}:</b> ${wh_badge}</div>
		</div>
	`;
	frm.dashboard.clear_headline();
	frm.dashboard.set_headline_alert(html);
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
		if (!r) {
			return;
		}
		// Point 16: Hide Party Asset Return link/icon in dashboard if user lacks financial return permission
		if (!r.can_view_return_links && frm.dashboard && frm.dashboard.transactions_area) {
			frm.dashboard.transactions_area
				.find('[data-doctype="Party Asset Return"]')
				.closest(".document-link")
				.hide();
		}

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

		// Point 15: Quick mobile button to assign/change Installation Manager
		if (r.can_assign_installer) {
			add_styled_button(
				frm,
				__("Assign Installation Manager"),
				() => {
					prompt_installation_manager(
						frm,
						(installation_manager) => {
							frappe
								.xcall(
									"mu_booking.mu_booking.doctype.party_booking.party_booking.assign_installation_manager",
									{
										name: frm.doc.name,
										installation_manager,
									}
								)
								.then(() => {
									frappe.show_alert({
										message: __("Installation Manager assigned and notified."),
										indicator: "green",
									});
									frm.reload_doc();
								});
						},
						__("Assign & Notify")
					);
				},
				"btn-info"
			);
		}

		// Points 2, 3, 4: Single button to record employee arrival time and mark assets Picked Up
		if (r.can_record_pickup) {
			add_styled_button(
				frm,
				__("Record Arrival & Pickup Assets"),
				() => {
					frappe.confirm(
						__("Confirm employee arrival and pickup of booking assets now?"),
						() => {
							frappe
								.xcall(
									"mu_booking.mu_booking.doctype.party_booking.party_booking.record_asset_pickup",
									{ name: frm.doc.name }
								)
								.then(() => {
									frappe.show_alert({
										message: __("Arrival time recorded and assets marked as Picked Up."),
										indicator: "green",
									});
									frm.reload_doc();
								});
						}
					);
				},
				"btn-success"
			);
		}

		// Point 17: Button for Installation Team to confirm asset return to warehouse
		if (r.can_confirm_warehouse_return) {
			add_styled_button(
				frm,
				__("Confirm Asset Return to Warehouse"),
				() => prompt_warehouse_return(frm),
				"btn-warning"
			);
		}

		// Point 16: Only Accountant / Manager / Admin sees Create Asset Return
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

function prompt_installation_manager(frm, callback, primary_label) {
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
				change() {
					const emp_id = dialog.get_value("installation_manager");
					if (!emp_id) {
						dialog.set_value("employee_name", "");
						dialog.set_value("cell_number", "");
						return;
					}
					frappe
						.xcall("mu_booking.mu_booking.doctype.party_booking.party_booking.get_employee_details", {
							employee: emp_id,
						})
						.then((emp) => {
							if (emp) {
								dialog.set_value("employee_name", emp.employee_name || "");
								dialog.set_value("cell_number", emp.cell_number || "");
							}
						});
				},
			},
			{
				fieldname: "employee_name",
				fieldtype: "Data",
				label: __("Installation Manager Name"),
				read_only: 1,
				default: frm.doc.installation_manager_name || "",
			},
			{
				fieldname: "cell_number",
				fieldtype: "Data",
				label: __("Installation Manager Mobile"),
				read_only: 1,
				default: frm.doc.installation_manager_mobile || "",
			},
		],
		primary_action_label: primary_label || __("Schedule"),
		primary_action(values) {
			dialog.hide();
			callback(values.installation_manager);
		},
	});
	dialog.show();
}

function prompt_warehouse_return(frm) {
	const asset_rows = (frm.doc.assets || []).filter((r) => r.asset_name);
	const fields = [
		{
			fieldname: "info_html",
			fieldtype: "HTML",
			options: `<div class="text-muted small" style="margin-bottom:8px;">${__(
				"Confirm that all booking assets have been returned to the warehouse. Check any asset below only if it was returned damaged."
			)}</div>`,
		},
	];

	asset_rows.forEach((row, idx) => {
		const title = frappe.utils.escape_html(row.asset_title || row.asset_name);
		const code = frappe.utils.escape_html(row.asset_name);
		fields.push({
			fieldname: `damaged_${idx}`,
			fieldtype: "Check",
			label: `${__("Damaged")}: ${title} (${code})`,
			default: 0,
		});
	});

	fields.push({
		fieldname: "notes",
		fieldtype: "Small Text",
		label: __("Warehouse Return Notes"),
	});

	const dialog = new frappe.ui.Dialog({
		title: __("Confirm Asset Return to Warehouse"),
		fields,
		primary_action_label: __("Confirm Return to Warehouse"),
		primary_action(values) {
			const damaged_assets = [];
			asset_rows.forEach((row, idx) => {
				if (values[`damaged_${idx}`]) {
					damaged_assets.push(row.asset_name);
				}
			});
			dialog.hide();
			frappe
				.xcall("mu_booking.mu_booking.doctype.party_booking.party_booking.confirm_warehouse_return", {
					name: frm.doc.name,
					damaged_assets,
					notes: values.notes || "",
				})
				.then(() => {
					frappe.show_alert({
						message: __("Assets confirmed returned to warehouse and booking status updated."),
						indicator: "green",
					});
					frm.reload_doc();
				});
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

// ---------------------------------------------------------------------------
// Point 1: Bilingual Employee Usage Guide (ع / E) at bottom of the document
// ---------------------------------------------------------------------------

function render_employee_guide(frm) {
	const field = frm.get_field("employee_guide_html");
	if (!field || !field.$wrapper) {
		return;
	}
	const wrapper = field.$wrapper;
	if (wrapper.attr("data-guide-rendered") === "1") {
		return;
	}
	wrapper.attr("data-guide-rendered", "1");

	const default_mode = "both";
	wrapper.html(`
		<div class="mu-booking-guide" style="border:1px solid var(--border-color);border-radius:var(--border-radius-md);padding:16px;background:var(--card-bg);margin-top:6px;">
			<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;border-bottom:1px solid var(--border-color);padding-bottom:12px;margin-bottom:14px;">
				<div style="font-weight:700;font-size:15px;">
					📖 دليل استخدام النظام للموظفين | Employee Usage Guide (ع / E)
				</div>
				<div class="btn-group btn-group-sm" role="group">
					<button type="button" class="btn btn-default mu-lang-btn active" data-lang="both">ع + E</button>
					<button type="button" class="btn btn-default mu-lang-btn" data-lang="ar">عربي (ع)</button>
					<button type="button" class="btn btn-default mu-lang-btn" data-lang="en">English (E)</button>
				</div>
			</div>

			<div class="mu-guide-grid" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(280px, 1fr));gap:16px;">
				<!-- Arabic Column -->
				<div class="mu-guide-col mu-guide-ar" dir="rtl" style="text-align:right;background:var(--control-bg);padding:14px;border-radius:8px;">
					<h5 style="margin-top:0;font-weight:700;color:var(--primary);">🇸🇦 أولاً: شرح الاستخدام باللغة العربية (ع)</h5>
					<div style="margin-bottom:10px;">
						<b>1. موظف المبيعات / مسؤول الحجوزات:</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>اختر <b>العميل</b>، وأدخل <b>موقع الحفلة</b> و<b>عنوان التركيب</b> ورابط خرائط جوجل، وأرفق <b>صورة مرجعية</b> للأوردر عند الحاجة.</li>
							<li>حدد <b>تاريخ الحفلة</b> (سيظهر اسم <b>اليوم</b> تلقائياً) و<b>وقت الحفلة</b>، ويمكن تعديل الموعد حتى بعد اعتماد الطلب.</li>
							<li>في جدول <b>الأصول</b>: اختر باركود الأصل والكمية المطلوبة؛ يتحقق النظام تلقائياً من الكمية المتاحة في نفس التاريخ فقط دون حجب التواريخ الأخرى.</li>
							<li>اضغط <b>تأكيد الحجز</b> لإشعار فريق التركيب تلقائياً داخل النظام، وتابع حالة الطلب وموقعه عبر <b>لوحة كانبان متابعة الطلبات</b>.</li>
						</ul>
					</div>
					<div style="margin-bottom:10px;">
						<b>2. مسؤول وفريق التركيب (عبر الجوال أو الكمبيوتر):</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>لتكليف مسؤول التركيب من الجوال اضغط زر <b>تكليف مسؤول التركيب</b> أو <b>جدولة التوصيل والتركيب</b> ليصله إشعار فوري.</li>
							<li>عند حضور الموظف للمستودع لاستلام الأصول، اضغط زر <b>تسجيل الوصول واستلام الأصول</b> لتسجيل وقت الوصول الفعلي وتحديث الحالة إلى <b>تم الاستلام</b>.</li>
							<li>بعد إتمام التركيب اضغط <b>تحديد كمنفذ</b>، وعند إعادة الأصول للمستودع اضغط <b>تأكيد إرجاع الأصل إلى المستودع</b> لتصبح الأصول متاحة فوراً.</li>
						</ul>
					</div>
					<div>
						<b>3. المحاسب (إرجاع التأمين وإغلاق الطلب):</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>عند وجود مبلغ تأمين، اضغط <b>إنشاء إرجاع أصل</b> لتسجيل رد التأمين أو خصم التلفيات ليتم إغلاق الأوردر آلياً.</li>
						</ul>
					</div>
				</div>

				<!-- English Column -->
				<div class="mu-guide-col mu-guide-en" dir="ltr" style="text-align:left;background:var(--control-bg);padding:14px;border-radius:8px;">
					<h5 style="margin-top:0;font-weight:700;color:var(--primary);">🇬🇧 Second: Employee Usage Guide in English (E)</h5>
					<div style="margin-bottom:10px;">
						<b>1. Sales / Booking Officer:</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>Select the <b>Customer</b>, enter the <b>Party Location</b>, <b>Installation Address</b>, and Google Maps link, and attach an <b>Order Reference Image</b> if needed.</li>
							<li>Set the <b>Party Date</b> (the <b>Day</b> name is filled automatically) and <b>Party Time</b>. Dates and times can be updated even after confirmation.</li>
							<li>In the <b>Assets</b> table, select the <b>Asset Barcode</b> and requested quantity; the system checks available quantity for that specific date without blocking other dates.</li>
							<li>Click <b>Confirm Booking</b> to automatically notify the installation team, and track order progress anytime via the <b>Order Tracking Kanban</b> board.</li>
						</ul>
					</div>
					<div style="margin-bottom:10px;">
						<b>2. Installation Manager & Team (Mobile / Desktop):</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>Use <b>Assign Installation Manager</b> or <b>Schedule Delivery / Installation</b> from your phone to assign the responsible employee and send an instant alert.</li>
							<li>When arriving at the warehouse to collect assets, click <b>Record Arrival & Pickup Assets</b> to log the exact arrival timestamp and mark status as <b>Picked Up</b>.</li>
							<li>After onsite completion, click <b>Mark as Executed</b>. Once assets are brought back, click <b>Confirm Asset Return to Warehouse</b> to release assets immediately.</li>
						</ul>
					</div>
					<div>
						<b>3. Accountant (Deposit Refund & Closure):</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>When a security deposit exists, click <b>Create Asset Return</b> to process the refund or damage deduction and automatically close the booking.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
	`);

	wrapper.find(".mu-lang-btn").on("click", function () {
		const lang = $(this).attr("data-lang") || default_mode;
		wrapper.find(".mu-lang-btn").removeClass("active btn-primary").addClass("btn-default");
		$(this).removeClass("btn-default").addClass("active btn-primary");
		if (lang === "ar") {
			wrapper.find(".mu-guide-ar").show();
			wrapper.find(".mu-guide-en").hide();
		} else if (lang === "en") {
			wrapper.find(".mu-guide-ar").hide();
			wrapper.find(".mu-guide-en").show();
		} else {
			wrapper.find(".mu-guide-ar").show();
			wrapper.find(".mu-guide-en").show();
		}
	});
}
