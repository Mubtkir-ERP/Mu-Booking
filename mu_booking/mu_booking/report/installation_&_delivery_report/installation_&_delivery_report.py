# Copyright (c) 2026, Mu Booking and contributors
# For license information, please see license.txt

from mu_booking.mu_booking.report.installation_and_delivery_report.installation_and_delivery_report import (
	execute as run_installation_and_delivery_report,
)


def execute(filters=None):
	return run_installation_and_delivery_report(filters)
