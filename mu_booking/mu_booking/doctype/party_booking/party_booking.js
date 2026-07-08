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
        calculate_recurring_fields(frm);
    },
    
    end_date: function(frm) {
        if (frm.doc.start_date && frm.doc.end_date) {
            let start = frappe.datetime.str_to_obj(frm.doc.start_date);
            let end = frappe.datetime.str_to_obj(frm.doc.end_date);
            let diff = frappe.datetime.get_day_diff(end, start) + 1;
            
            if (diff >= 1) {
                frm.set_value('number_of_days', diff);
            } else {
                frappe.msgprint(__('End Date cannot be before Start Date.'));
                frm.set_value('end_date', '');
            }
        }
    },
    
    number_of_days: function(frm) {
        if (frm.doc.start_date && frm.doc.number_of_days > 0) {
            let end = frappe.datetime.add_days(frm.doc.start_date, frm.doc.number_of_days - 1);
            frm.set_value('end_date', end);
        }
    }
});

function calculate_recurring_fields(frm) {
    if (frm.doc.start_date) {
        // If they enter start_date and already have end_date, calculate days
        if (frm.doc.end_date) {
            frm.events.end_date(frm);
        } 
        // Or if they have number of days, calculate end_date
        else if (frm.doc.number_of_days > 0) {
            frm.events.number_of_days(frm);
        }
    }
}
