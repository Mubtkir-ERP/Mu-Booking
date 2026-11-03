app_name = "mu_booking"
app_title = "Mu Booking"
app_publisher = "Mubtkir"
app_description = "Party & Event Asset Booking Management System - Mubtkir ERP (https://www.mubtkir.com)"
app_email = "apps@mubtkir.com"
app_license = "mit"
app_version = "1.1.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_js = "/assets/mu_booking/js/mu_booking.js"

# Installation / Migration
# ------------------------
before_install = "mu_booking.patches.v1_1.setup_kanban_and_properties.ensure_roles"
after_install = "mu_booking.patches.v1_1.setup_kanban_and_properties.execute"
after_migrate = ["mu_booking.patches.v1_1.setup_kanban_and_properties.execute"]

# Scheduled Tasks
# ---------------

scheduler_events = {
	"hourly": [
		"mu_booking.api.schedule_reminders"
	],
}

default_log_clearing_doctypes = {
	"Party Booking Reminder": 90
}

fixtures = [
	{"dt": "Custom Field", "filters": [["module", "=", "Mu Booking"]]},
	{"dt": "Property Setter", "filters": [["module", "=", "Mu Booking"]]}
]
