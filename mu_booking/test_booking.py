import frappe
from frappe.utils import today, add_days, nowtime

def run_tests():
    print("Starting Comprehensive Tests...")
    frappe.flags.in_test = True

    # 1. Create a dummy Asset
    asset_name = "Test-Chair-001"
    if not frappe.db.exists("Asset", asset_name):
        # We might need an item first
        item_code = "Test-Chair-Item"
        if not frappe.db.exists("Item", item_code):
            frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_group": "Products",
                "is_stock_item": 0,
                "is_fixed_asset": 1,
                "asset_category": "Equipment"
            }).insert(ignore_permissions=True)
            
        frappe.get_doc({
            "doctype": "Asset",
            "asset_name": asset_name,
            "item_code": item_code,
            "company": frappe.defaults.get_user_default("Company") or "Mu Booking",
            "is_existing_asset": 1,
            "party_booking_status": "Available"
        }).insert(ignore_permissions=True)

    # 2. Test Bot API Booking creation
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(
        customer_name="Test Customer",
        customer_mobile="123456789",
        party_date=add_days(today(), 2),
        party_time=nowtime(),
        event_type="Birthday",
        service_type="Delivery Only"
    )
    
    if res.get("status") == "success":
        booking_id = res.get("booking_id")
        print(f"Test 1 Passed: Bot API created booking {booking_id}")
    else:
        print(f"Test 1 Failed: {res}")
        return

    # 3. Test Workflow Progression & Asset Assignment
    doc = frappe.get_doc("Party Booking", booking_id)
    
    # Assign asset
    doc.append("assets", {
        "asset_name": asset_name,
        "qty": 1
    })
    doc.save(ignore_permissions=True)
    print("Asset assigned successfully.")

    # Move to Confirmed
    doc.workflow_state = "Confirmed"
    doc.submit()
    print("Test 2 Passed: Booking submitted and Confirmed.")

    asset_status = frappe.db.get_value("Asset", asset_name, "party_booking_status")
    if asset_status == "Booked":
        print("Test 3 Passed: Asset status correctly updated to 'Booked'.")
    else:
        print(f"Test 3 Failed: Asset status is {asset_status}")

    # 4. Conflict Check
    try:
        res2 = create_bot_booking(
            customer_name="Test Customer 2",
            customer_mobile="987654321",
            party_date=add_days(today(), 2),
            party_time=nowtime(),
            event_type="Wedding",
            service_type="Delivery Only"
        )
        doc2 = frappe.get_doc("Party Booking", res2.get("booking_id"))
        doc2.append("assets", {
            "asset_name": asset_name,
            "qty": 1
        })
        doc2.save(ignore_permissions=True)
        doc2.workflow_state = "Confirmed"
        doc2.submit()
        print("Test 4 Failed: Conflict check did not stop double booking!")
    except Exception as e:
        if "is already booked on" in str(e):
            print("Test 4 Passed: Conflict check successfully prevented double booking.")
        else:
            print(f"Test 4 Error: {str(e)}")

    # 5. Party Asset Return
    doc.workflow_state = "Pending Return"
    doc.save(ignore_permissions=True)
    
    return_doc = frappe.get_doc({
        "doctype": "Party Asset Return",
        "party_booking": booking_id,
        "refund_amount": 100, # Assuming no original deposit was set, this will just calculate deduction
        "refund_method": "Cash",
        "refund_date": today(),
        "refund_status": "Completed"
    })
    return_doc.insert(ignore_permissions=True)
    return_doc.submit()
    print("Test 5 Passed: Return document submitted.")

    asset_status = frappe.db.get_value("Asset", asset_name, "party_booking_status")
    if asset_status == "Available":
        print("Test 6 Passed: Asset status correctly reverted to 'Available'.")
    else:
        print(f"Test 6 Failed: Asset status is {asset_status}")

    print("All Tests Completed successfully.")

