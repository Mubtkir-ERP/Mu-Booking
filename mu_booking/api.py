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
    location_link=None,
    booking_type="One-time",
    customer_notes=None,
    receiver_mobile=None
):
    """
    API endpoint for the AI Bot to create a new Party Booking (Draft / Initial state).
    POST to: /api/method/mu_booking.api.create_bot_booking
    """
    # -- Input validation --
    if not customer_name or not customer_name.strip():
        return {"status": "error", "message": _("Customer name is required.")}

    if not customer_mobile or not customer_mobile.strip():
        return {"status": "error", "message": _("Customer mobile is required.")}

    # E01 FIX: Validate mobile number format (must contain only digits, +, spaces, or dashes)
    import re
    mobile_clean = customer_mobile.strip().replace(" ", "").replace("-", "")
    if not re.match(r'^\+?[0-9]{7,15}$', mobile_clean):
        return {"status": "error", "message": _("Customer mobile must be a valid phone number.")}

    if not party_date:
        return {"status": "error", "message": _("Party date is required.")}

    if getdate(party_date) < getdate(today()):
        return {"status": "error", "message": _("Party date cannot be in the past.")}

    if booking_type not in ("One-time", "Recurring"):
        return {"status": "error", "message": _("booking_type must be 'One-time' or 'Recurring'.")}

    if service_type not in ("Delivery Only", "Delivery and Installation"):
        return {"status": "error", "message": _("Invalid service_type.")}

    # E01 FIX: Deduplication — block duplicate bookings (same mobile + same date, not cancelled)
    existing = frappe.db.get_value(
        "Party Booking",
        {
            "customer_mobile": customer_mobile.strip(),
            "party_date": party_date,
            "docstatus": ["!=", 2]  # not cancelled
        },
        "name"
    )
    if existing:
        return {
            "status": "duplicate",
            "message": _("A booking already exists for this mobile number on the same date."),
            "existing_booking_id": existing
        }

    try:
        # Find or create customer
        customer_id = frappe.db.get_value("Customer", {"mobile_no": customer_mobile.strip()}, "name")
        if not customer_id:
            new_customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name.strip(),
                "customer_group": "Commercial",  # default
                "territory": "All Territories",  # default
                "customer_type": "Individual",
                "mobile_no": customer_mobile.strip()
            })
            new_customer.insert(ignore_permissions=True)
            customer_id = new_customer.name
        booking = frappe.get_doc({
            "doctype": "Party Booking",
            "customer": customer_id,
            "customer_name": customer_name.strip(),
            "customer_mobile": customer_mobile.strip(),
            "receiver_mobile": receiver_mobile,
            "party_date": party_date,
            "party_time": party_time,
            "event_type": event_type,
            "service_type": service_type,
            "party_location": party_location,
            "location_link": location_link,
            "booking_type": booking_type,
            "customer_notes": customer_notes
        })

        booking.insert(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": _("Booking created successfully."),
            "booking_id": booking.name
        }

    except Exception as e:
        frappe.log_error(title="Bot Booking API Error", message=frappe.get_traceback())
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }

@frappe.whitelist()
def schedule_reminders():
    """
    Hourly scheduled job to create 'Party Booking Reminder' records
    for bookings that are within the next 24 hours.
    """
    # Get tomorrow's date
    target_date = frappe.utils.add_days(frappe.utils.today(), 1)
    
    # Find bookings scheduled for tomorrow that are Confirmed
    bookings = frappe.get_all(
        "Party Booking",
        filters={
            "docstatus": 1,
            "workflow_state": ["in", ["Confirmed", "Delivery/Installation Scheduled"]],
            "party_date": target_date
        },
        fields=["name", "customer_name"]
    )
    
    for b in bookings:
        # Check if a reminder was already created for this booking
        if not frappe.db.exists("Party Booking Reminder", {"booking": b.name}):
            try:
                reminder = frappe.get_doc({
                    "doctype": "Party Booking Reminder",
                    "booking": b.name
                })
                reminder.insert(ignore_permissions=True)
            except Exception as e:
                frappe.log_error(f"Failed to create reminder for {b.name}: {str(e)}", "Schedule Reminders Error")

@frappe.whitelist(allow_guest=True)
def export_event_type():
    try:
        doc = frappe.get_doc("DocType", "Event Type")
        doc.custom = 0
        doc.module = "Mu Booking"
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return "SUCCESS"
    except Exception as e:
        return str(e)
