frappe.ui.form.on('Party Booking', {
    setup: function(frm) {
        frm.set_query("asset_name", "assets", function(doc, cdt, cdn) {
            return {
                filters: [
                    ['party_booking_status', 'not in', ['Damaged', 'Lost']]
                ]
            };
        });
        
        frm.set_query("alternative_asset", "sessions", function(doc, cdt, cdn) {
            return {
                filters: [
                    ['party_booking_status', 'not in', ['Damaged', 'Lost']]
                ]
            };
        });
    },
    
    start_date: function(frm) {
        if (frm.doc.recurring_pattern === 'Daily') {
            calculate_daily_end_date(frm);
        }
    },
    
    number_of_days: function(frm) {
        if (frm.doc.recurring_pattern === 'Daily') {
            calculate_daily_end_date(frm);
        }
    }
});

function calculate_daily_end_date(frm) {
    if (frm.doc.start_date && frm.doc.number_of_days > 0) {
        let end = frappe.datetime.add_days(frm.doc.start_date, frm.doc.number_of_days - 1);
        frm.set_value('end_date', end);
    }
}


