import re

import frappe
from frappe import _
from frappe.utils import getdate, today


@frappe.whitelist(allow_guest=True)
def create_bot_booking(
    customer_name,
    customer_mobile,
    party_date,
    party_time,
    event_type=None,
    service_type="Delivery Only",
    party_location=None,
    installation_address=None,
    location_link=None,
    booking_type="One-time",
    customer_notes=None,
    receiver_mobile=None,
):
    """
    API endpoint for the AI Bot to create a new Party Booking (Draft / Initial state).
    POST to: /api/method/mu_booking.api.create_bot_booking
    """
    # -- Input validation --
    if not isinstance(customer_name, str) or not customer_name.strip():
        return {"status": "error", "message": _("Customer name is required.")}

    customer_name_clean = customer_name.strip()[:140]

    if not isinstance(customer_mobile, str) or not customer_mobile.strip():
        return {"status": "error", "message": _("Customer mobile is required.")}

    # Validate mobile number format (must contain only digits, +, spaces, or dashes)
    mobile_clean = customer_mobile.strip().replace(" ", "").replace("-", "")
    if not re.match(r"^\+?[0-9]{7,15}$", mobile_clean):
        return {"status": "error", "message": _("Customer mobile must be a valid phone number.")}

    if not party_date or not isinstance(party_date, str):
        return {"status": "error", "message": _("Party date is required.")}

    try:
        parsed_party_date = getdate(party_date)
    except Exception:
        return {"status": "error", "message": _("Party date is required.")}

    if parsed_party_date < getdate(today()):
        return {"status": "error", "message": _("Party date cannot be in the past.")}

    if booking_type not in ("One-time", "Recurring"):
        return {"status": "error", "message": _("booking_type must be 'One-time' or 'Recurring'.")}

    if service_type not in ("Delivery Only", "Delivery and Installation"):
        return {"status": "error", "message": _("Invalid service_type.")}

    if location_link and isinstance(location_link, str):
        location_link = location_link.strip()
        if location_link and not re.match(r"^https?://", location_link, flags=re.IGNORECASE):
            return {
                "status": "error",
                "message": _("Invalid map URL. Must start with http:// or https://"),
            }

    # Deduplication — block duplicate bookings (same mobile + same date, not cancelled)
    existing = frappe.db.get_value(
        "Party Booking",
        {
            "customer_mobile": customer_mobile.strip(),
            "party_date": party_date,
            "docstatus": ["!=", 2],  # not cancelled
        },
        "name",
    )
    if existing:
        resp = {
            "status": "duplicate",
            "message": _("A booking already exists for this mobile number on the same date."),
        }
        if frappe.session.user != "Guest":
            resp["existing_booking_id"] = existing
        return resp

    try:
        # Find or create customer
        customer_id = frappe.db.get_value("Customer", {"mobile_no": customer_mobile.strip()}, "name")
        if not customer_id:
            new_customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name_clean,
                "customer_group": "Commercial",
                "territory": "All Territories",
                "customer_type": "Individual",
                "mobile_no": customer_mobile.strip(),
            })
            new_customer.insert(ignore_permissions=True)
            customer_id = new_customer.name

        booking = frappe.get_doc({
            "doctype": "Party Booking",
            "customer": customer_id,
            "customer_name": customer_name_clean,
            "customer_mobile": customer_mobile.strip(),
            "receiver_mobile": (receiver_mobile or "").strip()[:30] if isinstance(receiver_mobile, str) else None,
            "party_date": party_date,
            "party_time": party_time,
            "event_type": event_type,
            "service_type": service_type,
            "party_location": (party_location or "").strip()[:140] if isinstance(party_location, str) else None,
            "installation_address": (installation_address or "").strip()[:500] if isinstance(installation_address, str) else None,
            "location_link": location_link,
            "booking_type": booking_type,
            "customer_notes": (customer_notes or "").strip()[:1000] if isinstance(customer_notes, str) else None,
        })

        booking.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Booking created successfully."),
            "booking_id": booking.name,
        }

    except Exception:
        frappe.log_error(title="Bot Booking API Error", message=frappe.get_traceback())
        return {
            "status": "error",
            "message": _("An unexpected error occurred while creating the booking."),
        }


def schedule_reminders():
    """
    Hourly scheduled job to create 'Party Booking Reminder' records
    for bookings that are within the next 24 hours.
    """
    target_date = frappe.utils.add_days(frappe.utils.today(), 1)

    bookings = frappe.get_all(
        "Party Booking",
        filters={
            "docstatus": 1,
            "status": ["in", ["Confirmed", "Delivery/Installation Scheduled"]],
            "party_date": target_date,
        },
        fields=["name", "customer_name"],
    )

    for b in bookings:
        if not frappe.db.exists("Party Booking Reminder", {"booking": b.name}):
            try:
                reminder = frappe.get_doc({
                    "doctype": "Party Booking Reminder",
                    "booking": b.name,
                })
                reminder.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(
                    f"Failed to create reminder for {b.name}: {str(e)}", "Schedule Reminders Error"
                )
