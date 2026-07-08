import frappe

def create_doctypes():
    def create_custom_field_in_asset():
        if not frappe.db.exists("Custom Field", "Asset-party_booking_status"):
            doc = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Asset",
                "fieldname": "party_booking_status",
                "label": "Party Booking Status",
                "fieldtype": "Select",
                "options": "Available\nBooked\nDamaged",
                "insert_after": "status",
                "default": "Available"
            })
            doc.insert(ignore_permissions=True)
            print("Custom Field 'party_booking_status' created in Asset.")

    def create_doc(d):
        if not frappe.db.exists("DocType", d["name"]):
            doc = frappe.get_doc(d)
            doc.insert(ignore_permissions=True)
            print(f"DocType '{d['name']}' created.")
        else:
            print(f"DocType '{d['name']}' already exists.")

    create_doc({
        "doctype": "DocType",
        "module": "Mu Booking",
        "custom": 0,
        "name": "Party Booking Asset",
        "istable": 1,
        "fields": [
            {"fieldname": "asset_type", "fieldtype": "Link", "options": "Item Group", "label": "Asset Type", "in_list_view": 1},
            {"fieldname": "asset_name", "fieldtype": "Link", "options": "Asset", "label": "Asset", "in_list_view": 1},
            {"fieldname": "qty", "fieldtype": "Int", "label": "Quantity", "default": "1", "in_list_view": 1},
            {"fieldname": "asset_booking_status", "fieldtype": "Select", "label": "Booking Status", "options": "Booked\nDelivered\nReturned\nDamaged", "default": "Booked", "in_list_view": 1},
            {"fieldname": "notes", "fieldtype": "Small Text", "label": "Notes"}
        ]
    })

    create_doc({
        "doctype": "DocType",
        "module": "Mu Booking",
        "custom": 0,
        "name": "Party Booking Session",
        "istable": 1,
        "fields": [
            {"fieldname": "session_date", "fieldtype": "Date", "label": "Session Date", "in_list_view": 1, "reqd": 1},
            {"fieldname": "session_time", "fieldtype": "Time", "label": "Session Time", "in_list_view": 1, "reqd": 1},
            {"fieldname": "session_status", "fieldtype": "Select", "label": "Status", "options": "Scheduled\nExecuted\nCancelled", "default": "Scheduled", "in_list_view": 1}
        ]
    })

    create_doc({
        "doctype": "DocType",
        "module": "Mu Booking",
        "custom": 0,
        "name": "Party Booking",
        "autoname": "PB-.YYYY.-.#####",
        "is_submittable": 1,
        "fields": [
            {"fieldname": "customer_section", "fieldtype": "Section Break", "label": "Customer Information"},
            {"fieldname": "customer", "fieldtype": "Link", "options": "Customer", "label": "Customer", "reqd": 1, "in_list_view": 1},
            {"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name", "read_only": 1, "fetch_from": "customer.customer_name", "in_list_view": 1},
            {"fieldname": "customer_mobile", "fieldtype": "Data", "label": "Customer Mobile", "read_only": 1, "fetch_from": "customer.mobile_no", "in_list_view": 1},
            {"fieldname": "receiver_mobile", "fieldtype": "Data", "label": "Receiver Mobile"},
            {"fieldname": "cb_1", "fieldtype": "Column Break"},
            {"fieldname": "party_location", "fieldtype": "Data", "label": "Party Location"},
            {"fieldname": "location_link", "fieldtype": "Data", "label": "Location Link (Google Maps)"},
            {"fieldname": "customer_notes", "fieldtype": "Small Text", "label": "Customer Notes"},
            
            {"fieldname": "booking_section", "fieldtype": "Section Break", "label": "Booking Information"},
            {"fieldname": "event_type", "fieldtype": "Data", "label": "Event Type"},
            {"fieldname": "service_type", "fieldtype": "Select", "label": "Service Type", "options": "Delivery Only\nDelivery and Installation", "default": "Delivery Only"},
            {"fieldname": "booking_type", "fieldtype": "Select", "label": "Booking Type", "options": "One-time\nRecurring", "default": "One-time"},
            {"fieldname": "cb_2", "fieldtype": "Column Break"},
            {"fieldname": "party_date", "fieldtype": "Date", "label": "Party Date", "reqd": 1},
            {"fieldname": "party_time", "fieldtype": "Time", "label": "Party Time", "reqd": 1},
            {"fieldname": "booking_officer", "fieldtype": "Link", "options": "Employee", "label": "Booking Officer"},
            
            {"fieldname": "recurring_section", "fieldtype": "Section Break", "label": "Recurring Booking Details", "depends_on": "eval:doc.booking_type=='Recurring'"},
            {"fieldname": "recurring_pattern", "fieldtype": "Select", "label": "Recurring Pattern", "options": "\nDaily\nWeekly\nMonthly\nManual"},
            {"fieldname": "start_date", "fieldtype": "Date", "label": "Start Date"},
            {"fieldname": "number_of_days", "fieldtype": "Int", "label": "Number of Days/Sessions"},
            {"fieldname": "cb_3", "fieldtype": "Column Break"},
            {"fieldname": "end_date", "fieldtype": "Date", "label": "End Date"},
            
            {"fieldname": "sessions_section", "fieldtype": "Section Break", "label": "Sessions", "depends_on": "eval:doc.booking_type=='Recurring'"},
            {"fieldname": "sessions", "fieldtype": "Table", "options": "Party Booking Session", "label": "Booking Sessions"},

            {"fieldname": "assets_section", "fieldtype": "Section Break", "label": "Booking Assets"},
            {"fieldname": "assets", "fieldtype": "Table", "options": "Party Booking Asset", "label": "Assets"},

            {"fieldname": "financial_section", "fieldtype": "Section Break", "label": "Financial Information"},
            {"fieldname": "security_deposit", "fieldtype": "Currency", "label": "Security Deposit"},
            {"fieldname": "deposit_status", "fieldtype": "Select", "label": "Deposit Status", "options": "Pending\nRefunded\nPartially Deducted", "default": "Pending"},
            {"fieldname": "cb_4", "fieldtype": "Column Break"},
            {"fieldname": "invoice_ref", "fieldtype": "Link", "options": "Sales Invoice", "label": "Invoice Reference"}
        ]
    })

    create_doc({
        "doctype": "DocType",
        "module": "Mu Booking",
        "custom": 0,
        "name": "Party Asset Return",
        "autoname": "PAR-.YYYY.-.#####",
        "is_submittable": 1,
        "fields": [
            {"fieldname": "party_booking", "fieldtype": "Link", "options": "Party Booking", "label": "Party Booking", "reqd": 1, "in_list_view": 1},
            {"fieldname": "customer", "fieldtype": "Link", "options": "Customer", "label": "Customer", "read_only": 1, "fetch_from": "party_booking.customer", "in_list_view": 1},
            {"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name", "read_only": 1, "fetch_from": "party_booking.customer_name", "in_list_view": 1},
            {"fieldname": "receiver_mobile", "fieldtype": "Data", "label": "Receiver Mobile", "read_only": 1, "fetch_from": "party_booking.receiver_mobile"},
            {"fieldname": "cb_1", "fieldtype": "Column Break"},
            {"fieldname": "original_deposit", "fieldtype": "Currency", "label": "Original Deposit", "read_only": 1, "fetch_from": "party_booking.security_deposit"},
            
            {"fieldname": "refund_section", "fieldtype": "Section Break", "label": "Refund Details"},
            {"fieldname": "refund_amount", "fieldtype": "Currency", "label": "Refund Amount"},
            {"fieldname": "deduction_amount", "fieldtype": "Currency", "label": "Deduction Amount", "read_only": 1},
            {"fieldname": "deduction_reason", "fieldtype": "Small Text", "label": "Deduction Reason", "depends_on": "eval:doc.deduction_amount > 0"},
            {"fieldname": "cb_2", "fieldtype": "Column Break"},
            {"fieldname": "refund_method", "fieldtype": "Select", "options": "Cash\nBank Transfer", "label": "Refund Method"},
            {"fieldname": "payment_account", "fieldtype": "Link", "options": "Account", "label": "Payment Account"},
            {"fieldname": "refund_date", "fieldtype": "Date", "label": "Refund Date"},
            {"fieldname": "refund_status", "fieldtype": "Select", "options": "Pending\nCompleted\nPartially Deducted", "label": "Refund Status", "default": "Pending"},
            
            {"fieldname": "notes_section", "fieldtype": "Section Break", "label": "Notes"},
            {"fieldname": "accountant_notes", "fieldtype": "Text", "label": "Accountant Notes"}
        ]
    })
    
    create_custom_field_in_asset()
    frappe.db.commit()
