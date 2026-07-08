frappe.ui.form.on('Party Booking', {
    setup: function(frm) {
        // Filter the asset_name in the assets child table
        // Only show assets where party_booking_status is 'Available'
        frm.set_query("asset_name", "assets", function(doc, cdt, cdn) {
            return {
                filters: {
                    'party_booking_status': 'Available'
                }
            };
        });
    }
});
