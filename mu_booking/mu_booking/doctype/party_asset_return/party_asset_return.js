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
		render_return_employee_guide(frm);
	},
	refund_amount(frm) {
		const original = Number(frm.doc.original_deposit || 0);
		const refund = Number(frm.doc.refund_amount || 0);
		frm.set_value("deduction_amount", Math.max(original - refund, 0));
	},
});

function render_return_employee_guide(frm) {
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
					📖 دليل استخدام شاشة إرجاع الأصول للموظفين | Asset Return Usage Guide (ع / E)
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
						<b>1. اختيار الحجز والتحقق من التأمين:</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>اختر رقم <b>حجز الحفلة</b> (أو أنشئ المستند مباشرة من داخل الحجز عندما تكون حالته <b>بانتظار الإرجاع</b>).</li>
							<li>سيجلب النظام تلقائياً <b>اسم العميل</b>، <b>جوال المستلم</b>، وقيمة <b>التأمين الأصلي</b> المسجلة في الحجز.</li>
						</ul>
					</div>
					<div style="margin-bottom:10px;">
						<b>2. احتساب مبلغ الاسترجاع والخصم:</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>أدخل <b>مبلغ الاسترجاع</b> الفعلي الذي سيُرد للعميل؛ سيقوم النظام تلقائياً بحساب <b>مبلغ الخصم</b> (التأمين الأصلي ناقص مبلغ الاسترجاع).</li>
							<li>في حال وجود خصم، اكتب <b>سبب الخصم</b> بوضوح (مع ذكر كود أو اسم الأصل التالف إن وجد).</li>
						</ul>
					</div>
					<div>
						<b>3. طريقة الاسترجاع واعتماد المستند:</b>
						<ul style="padding-right:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>حدد <b>طريقة الاسترجاع</b> (نقدي / تحويل بنكي)، <b>حساب الدفع</b>، <b>تاريخ الاسترجاع</b>، و<b>حالة الاسترجاع</b> (مكتمل / مخصوم جزئياً).</li>
							<li>أضف <b>ملاحظات المحاسب</b> عند الحاجة، ثم اضغط <b>حفظ</b> ثم <b>اعتماد (Submit)</b> ليتم تحرير الأصول وإغلاق الحجز تلقائياً.</li>
						</ul>
					</div>
				</div>

				<!-- English Column -->
				<div class="mu-guide-col mu-guide-en" dir="ltr" style="text-align:left;background:var(--control-bg);padding:14px;border-radius:8px;">
					<h5 style="margin-top:0;font-weight:700;color:var(--primary);">🇬🇧 Second: Employee Usage Guide in English (E)</h5>
					<div style="margin-bottom:10px;">
						<b>1. Select Booking & Verify Deposit:</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>Select the <b>Party Booking</b> (or create this document directly from a booking in <b>Pending Return</b> status).</li>
							<li>The system automatically fetches the <b>Customer Name</b>, <b>Receiver Mobile</b>, and <b>Original Deposit</b> amount.</li>
						</ul>
					</div>
					<div style="margin-bottom:10px;">
						<b>2. Calculate Refund & Deduction:</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>Enter the actual <b>Refund Amount</b> to be returned to the customer; the system automatically calculates the <b>Deduction Amount</b>.</li>
							<li>If there is a deduction, enter the <b>Deduction Reason</b> clearly (mentioning the damaged asset code or name if applicable).</li>
						</ul>
					</div>
					<div>
						<b>3. Refund Method & Submission:</b>
						<ul style="padding-left:18px;margin:4px 0 0 0;line-height:1.7;">
							<li>Choose the <b>Refund Method</b> (Cash / Bank Transfer), <b>Payment Account</b>, <b>Refund Date</b>, and <b>Refund Status</b> (Completed / Partially Deducted).</li>
							<li>Add any <b>Accountant Notes</b>, then click <b>Save</b> and <b>Submit</b> to release the booking assets and automatically close the order.</li>
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
