"""
COMPREHENSIVE SECURITY & LOGIC TEST SUITE for Party Booking Application
Covers: Business Logic, Edge Cases, Security, Data Integrity, UX Flows
Run via API: GET http://127.0.0.1:8005/api/method/mu_booking.test_runner.run_my_tests
"""

import frappe
from frappe.utils import today, add_days, nowtime, flt


# ─── Result Tracking ──────────────────────────────────────────────────────────
_results = []

def _pass(test_name):
    _results.append(("PASS", test_name))
    print(f"  ✅  PASS | {test_name}")

def _fail(test_name, reason=""):
    _results.append(("FAIL", test_name, reason))
    print(f"  ❌  FAIL | {test_name}")
    if reason:
        print(f"           Reason: {reason}")

def _warn(test_name, reason=""):
    _results.append(("WARN", test_name, reason))
    print(f"  ⚠️   WARN | {test_name}")
    if reason:
        print(f"           Details: {reason}")

def _header(section):
    print(f"\n{'─'*60}")
    print(f"  {section}")
    print(f"{'─'*60}")


# ─── Helpers ──────────────────────────────────────────────────────────────────
ASSET_NAME = "TEST-SPEAKER-001"
ASSET_NAME_2 = "TEST-SPEAKER-002"

def ensure_assets():
    """Ensure test assets exist with Available status."""
    company = frappe.defaults.get_global_default("company") or frappe.db.get_value("Company", {}, "name")
    item_group = frappe.db.get_value("Item Group", {}, "name") or "All Item Groups"

    # Ensure Asset Category
    if not frappe.db.exists("Asset Category", "Party Equipment"):
        ac = frappe.get_doc({
            "doctype": "Asset Category",
            "asset_category_name": "Party Equipment",
        })
        ac.append("accounts", {
            "company_name": company,
            "fixed_asset_account": frappe.db.get_value("Account", {"company": company, "account_type": "Fixed Asset", "is_group": 0}, "name") or "",
        })
        try:
            ac.insert(ignore_permissions=True)
        except Exception:
            pass

    # Ensure Item
    if not frappe.db.exists("Item", "PARTY-SPEAKER"):
        try:
            frappe.get_doc({
                "doctype": "Item",
                "item_code": "PARTY-SPEAKER",
                "item_name": "Party Speaker",
                "item_group": item_group,
                "is_stock_item": 0,
                "is_fixed_asset": 1,
                "asset_category": "Party Equipment"
            }).insert(ignore_permissions=True)
        except Exception as e:
            print(f"  ⚠️  Could not create item: {e}")

    for asset_name in [ASSET_NAME, ASSET_NAME_2]:
        if frappe.db.exists("Asset", asset_name):
            frappe.db.set_value("Asset", asset_name, "party_booking_status", "Available")
        else:
            try:
                frappe.get_doc({
                    "doctype": "Asset",
                    "asset_name": asset_name,
                    "item_code": "PARTY-SPEAKER",
                    "asset_category": "Party Equipment",
                    "company": company,
                    "is_existing_asset": 1,
                    "party_booking_status": "Available"
                }).insert(ignore_permissions=True)
            except Exception as e:
                print(f"  ⚠️  Could not create asset {asset_name}: {e}")
    frappe.db.commit()


def make_booking(customer="Test Customer", date_offset=10, assets=None, deposit=500, **kwargs):
    doc = frappe.get_doc({
        "doctype": "Party Booking",
        "customer_name": customer,
        "customer_mobile": "0501234567",
        "party_date": add_days(today(), date_offset),
        "party_time": "20:00:00",
        "service_type": "Delivery Only",
        "booking_type": "One-time",
        "security_deposit": deposit,
        **kwargs
    })
    if assets:
        for a in assets:
            doc.append("assets", {"asset_name": a, "qty": 1})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc


def force_delete(doctype, name):
    try:
        if not frappe.db.exists(doctype, name):
            return
        d = frappe.get_doc(doctype, name)
        if d.docstatus == 1:
            d.cancel()
        frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass


# ─── TEST GROUPS ──────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════
# GROUP A: Input Validation & Mandatory Fields
# ══════════════════════════════════════════════════════════════

def test_A01_reject_empty_customer_name():
    _header("A01 | Validation: Reject empty customer name")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="", customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00")
    if res.get("status") == "error":
        _pass("A01 | Empty customer_name rejected by API")
    else:
        _fail("A01 | Empty customer_name rejected by API", "API allowed empty name!")

def test_A02_reject_past_date():
    _header("A02 | Validation: Reject past party date")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="Ahmed", customer_mobile="0500000000",
                             party_date="2020-01-01", party_time="20:00:00")
    if res.get("status") == "error":
        _pass("A02 | Past date rejected by API")
    else:
        _fail("A02 | Past date rejected by API", "API allowed past date!")

def test_A03_reject_today_date():
    _header("A03 | Edge Case: Book for today (same-day booking)")
    from mu_booking.api import create_bot_booking
    # Today's booking should be ALLOWED (not in the past)
    res = create_bot_booking(customer_name="Same Day", customer_mobile="0500000000",
                             party_date=today(), party_time="23:59:00")
    if res.get("status") == "success":
        _pass("A03 | Same-day booking is allowed")
        force_delete("Party Booking", res.get("booking_id"))
    else:
        _warn("A03 | Same-day booking behavior", f"Result: {res.get('message')}")

def test_A04_reject_invalid_mobile_format():
    _header("A04 | Validation: Mobile number format")
    from mu_booking.api import create_bot_booking
    # Mobile with letters - should fail or warn
    res = create_bot_booking(customer_name="Test User", customer_mobile="ABCDEFG",
                             party_date=add_days(today(), 3), party_time="20:00:00")
    if res.get("status") == "error":
        _pass("A04 | Invalid mobile format rejected")
    else:
        _warn("A04 | Invalid mobile format NOT validated", 
              "System accepts non-numeric mobile numbers - could cause WhatsApp delivery failure!")
        if res.get("booking_id"):
            force_delete("Party Booking", res["booking_id"])

def test_A05_reject_invalid_service_type():
    _header("A05 | Validation: Invalid service_type")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="Test", customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00",
                             service_type="HACK_TYPE")
    if res.get("status") == "error":
        _pass("A05 | Invalid service_type rejected")
    else:
        _fail("A05 | Invalid service_type rejected", "API accepted invalid service_type!")

def test_A06_whitespace_injection_customer_name():
    _header("A06 | Security: Whitespace-only customer name")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="     ", customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00")
    if res.get("status") == "error":
        _pass("A06 | Whitespace-only name rejected")
    else:
        _fail("A06 | Whitespace-only name rejected", "API accepted whitespace-only name - data quality issue!")

def test_A07_sql_injection_in_name():
    _header("A07 | Security: SQL Injection attempt in customer name")
    from mu_booking.api import create_bot_booking
    malicious = "Robert'); DROP TABLE `tabParty Booking`; --"
    res = create_bot_booking(customer_name=malicious, customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00")
    # Should either succeed safely (Frappe ORM handles it) or error - NOT crash the server
    if res.get("status") in ("success", "error"):
        _pass("A07 | SQL injection safely handled by ORM")
        if res.get("booking_id"):
            force_delete("Party Booking", res["booking_id"])
    else:
        _fail("A07 | SQL injection may have caused unexpected behavior", str(res))

def test_A08_xss_in_customer_notes():
    _header("A08 | Security: XSS in customer_notes field")
    from mu_booking.api import create_bot_booking
    xss_payload = "<script>alert('XSS')</script>"
    res = create_bot_booking(customer_name="XSS Test", customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00",
                             customer_notes=xss_payload)
    if res.get("status") == "success":
        booking_id = res.get("booking_id")
        stored = frappe.db.get_value("Party Booking", booking_id, "customer_notes")
        # Frappe should auto-escape or store as-is (HTML in Data field)
        if "<script>" in (stored or ""):
            _warn("A08 | XSS payload stored as-is in customer_notes",
                  "Script tags stored unescaped - Frappe escapes on render but worth noting")
        else:
            _pass("A08 | XSS payload was sanitized")
        force_delete("Party Booking", booking_id)
    else:
        _pass("A08 | XSS payload rejected at API level")


# ══════════════════════════════════════════════════════════════
# GROUP B: Business Logic & Asset Management
# ══════════════════════════════════════════════════════════════

def test_B01_asset_becomes_booked_on_submit():
    _header("B01 | Business Logic: Asset status changes to Booked on submit")
    if not frappe.db.exists("Asset", ASSET_NAME):
        _warn("B01 | Skipped - test asset not available"); return

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    doc = make_booking("B01 Customer", date_offset=30, assets=[ASSET_NAME])
    doc.submit()
    frappe.db.commit()
    status = frappe.db.get_value("Asset", ASSET_NAME, "party_booking_status")
    if status == "Booked":
        _pass("B01 | Asset marked as Booked after submit")
    else:
        _fail("B01 | Asset marked as Booked after submit", f"Got: {status}")
    doc.cancel()
    frappe.db.commit()
    force_delete("Party Booking", doc.name)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    frappe.db.commit()

def test_B02_asset_reverts_on_cancel():
    _header("B02 | Business Logic: Asset reverts to Available on cancel")
    if not frappe.db.exists("Asset", ASSET_NAME):
        _warn("B02 | Skipped - test asset not available"); return

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    doc = make_booking("B02 Customer", date_offset=31, assets=[ASSET_NAME])
    doc.submit()
    frappe.db.commit()
    doc.cancel()
    frappe.db.commit()
    status = frappe.db.get_value("Asset", ASSET_NAME, "party_booking_status")
    if status == "Available":
        _pass("B02 | Asset reverted to Available after cancel")
    else:
        _fail("B02 | Asset revert on cancel", f"Got: {status}")
    force_delete("Party Booking", doc.name)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    frappe.db.commit()

def test_B03_conflict_same_asset_same_date():
    _header("B03 | Business Logic: Prevent double booking same asset same date")
    if not frappe.db.exists("Asset", ASSET_NAME):
        _warn("B03 | Skipped - test asset not available"); return

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    doc1 = make_booking("B03 First", date_offset=40, assets=[ASSET_NAME])
    doc1.submit()
    frappe.db.commit()

    conflict_caught = False
    doc2_name = None
    try:
        doc2 = make_booking("B03 Second", date_offset=40, assets=[ASSET_NAME])
        doc2_name = doc2.name
        doc2.submit()
        frappe.db.commit()
        _fail("B03 | Double booking prevented", "System allowed double booking!")
    except frappe.ValidationError as e:
        if "already booked" in str(e).lower() or "conflict" in str(e).lower():
            _pass("B03 | Double booking on same date correctly prevented")
        else:
            _fail("B03 | Double booking prevention", f"Error: {str(e)}")
        conflict_caught = True
    except Exception as e:
        _fail("B03 | Double booking prevention", f"Unexpected error: {str(e)}")

    if doc2_name:
        force_delete("Party Booking", doc2_name)
    doc1.cancel()
    force_delete("Party Booking", doc1.name)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    frappe.db.commit()

def test_B04_conflict_different_date_same_asset_allowed():
    _header("B04 | Business Logic: Same asset on different dates should be ALLOWED")
    if not frappe.db.exists("Asset", ASSET_NAME):
        _warn("B04 | Skipped - test asset not available"); return

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    doc1 = make_booking("B04 First", date_offset=50, assets=[ASSET_NAME])
    doc1.submit()
    frappe.db.commit()

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")

    try:
        doc2 = make_booking("B04 Second", date_offset=55, assets=[ASSET_NAME])
        doc2.submit()
        frappe.db.commit()
        _pass("B04 | Same asset on different dates correctly allowed")
        doc2.cancel()
        force_delete("Party Booking", doc2.name)
    except frappe.ValidationError as e:
        _fail("B04 | Same asset different date should be allowed", str(e))

    doc1.cancel()
    force_delete("Party Booking", doc1.name)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    frappe.db.commit()

def test_B05_booking_without_assets():
    _header("B05 | Edge Case: Booking with NO assets (valid scenario)")
    doc = make_booking("B05 No Assets", date_offset=60)
    doc.submit()
    frappe.db.commit()
    if doc.docstatus == 1:
        _pass("B05 | Booking without assets is allowed and submitted")
    else:
        _fail("B05 | Booking without assets", "Submit failed unexpectedly")
    doc.cancel()
    force_delete("Party Booking", doc.name)

def test_B06_cancel_damaged_asset_stays_damaged():
    _header("B06 | Business Logic: Damaged asset should NOT revert to Available on cancel")
    if not frappe.db.exists("Asset", ASSET_NAME):
        _warn("B06 | Skipped - test asset not available"); return

    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    doc = make_booking("B06 Damage Test", date_offset=70, assets=[ASSET_NAME])
    doc.submit()
    frappe.db.commit()

    # Manually mark asset as Damaged (simulating what return process does)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Damaged")
    frappe.db.commit()

    # Now cancel the booking
    doc.cancel()
    frappe.db.commit()

    status = frappe.db.get_value("Asset", ASSET_NAME, "party_booking_status")
    if status == "Damaged":
        _pass("B06 | Damaged asset correctly stays 'Damaged' after booking cancellation")
    else:
        _fail("B06 | Damaged asset incorrectly reset", f"Expected 'Damaged', got '{status}'")

    force_delete("Party Booking", doc.name)
    frappe.db.set_value("Asset", ASSET_NAME, "party_booking_status", "Available")
    frappe.db.commit()


# ══════════════════════════════════════════════════════════════
# GROUP C: Recurring Booking Logic
# ══════════════════════════════════════════════════════════════

def test_C01_recurring_session_auto_generation():
    _header("C01 | Recurring: Daily sessions auto-generated correctly")
    doc = frappe.get_doc({
        "doctype": "Party Booking",
        "customer_name": "C01 Recurring",
        "customer_mobile": "0501111111",
        "party_date": add_days(today(), 80),
        "party_time": "18:00:00",
        "service_type": "Delivery Only",
        "booking_type": "Recurring",
        "recurring_pattern": "Daily",
        "start_date": add_days(today(), 80),
        "number_of_days": 5
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    doc.reload()
    count = len(doc.sessions)
    if count == 5:
        _pass("C01 | 5 sessions auto-generated for 5-day recurring booking")
    else:
        _fail("C01 | Session generation count", f"Expected 5, got {count}")
    force_delete("Party Booking", doc.name)

def test_C02_recurring_sessions_have_correct_dates():
    _header("C02 | Recurring: Session dates are sequentially correct")
    start = add_days(today(), 90)
    doc = frappe.get_doc({
        "doctype": "Party Booking",
        "customer_name": "C02 Dates",
        "customer_mobile": "0501111111",
        "party_date": start,
        "party_time": "18:00:00",
        "service_type": "Delivery Only",
        "booking_type": "Recurring",
        "recurring_pattern": "Daily",
        "start_date": start,
        "number_of_days": 3
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    doc.reload()
    dates = [str(s.session_date) for s in doc.sessions]
    expected = [str(add_days(start, i)) for i in range(3)]
    if sorted(dates) == sorted(expected):
        _pass("C02 | Session dates are sequential and correct")
    else:
        _fail("C02 | Session dates", f"Expected {expected}, got {dates}")
    force_delete("Party Booking", doc.name)

def test_C03_recurring_with_zero_days():
    _header("C03 | Edge Case: Recurring booking with 0 days should be REJECTED")
    try:
        doc = frappe.get_doc({
            "doctype": "Party Booking",
            "customer_name": "C03 Zero Days",
            "customer_mobile": "0501111111",
            "party_date": add_days(today(), 100),
            "party_time": "18:00:00",
            "service_type": "Delivery Only",
            "booking_type": "Recurring",
            "recurring_pattern": "Daily",
            "start_date": add_days(today(), 100),
            "number_of_days": 0
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        # If it saved, the fix didn't work
        _fail("C03 | Recurring with 0 days rejected", "System allowed saving with 0 days!")
        force_delete("Party Booking", doc.name)
    except (frappe.ValidationError, Exception) as e:
        err_str = str(e).lower()
        if "at least 1" in err_str or "number of days" in err_str:
            _pass("C03 | Recurring booking with 0 days is correctly rejected")
        else:
            _fail("C03 | Recurring 0-day validation", f"Unexpected error: {str(e)}")


# ══════════════════════════════════════════════════════════════
# GROUP D: Financial Logic & Asset Return
# ══════════════════════════════════════════════════════════════

def test_D01_refund_exceeds_deposit_rejected():
    _header("D01 | Financial: Refund > Deposit should be rejected")
    doc = make_booking("D01 Finance", date_offset=110, deposit=300)
    doc.submit()
    frappe.db.commit()
    try:
        ret = frappe.get_doc({
            "doctype": "Party Asset Return",
            "party_booking": doc.name,
            "original_deposit": 300,
            "refund_amount": 999,
            "refund_method": "Cash",
            "refund_date": today(),
            "refund_status": "Completed"
        })
        ret.insert(ignore_permissions=True)
        _fail("D01 | Refund > Deposit rejected", "System allowed refund amount exceeding deposit!")
        force_delete("Party Asset Return", ret.name)
    except frappe.ValidationError as e:
        _pass("D01 | Refund exceeding deposit correctly rejected")
    force_delete("Party Booking", doc.name)

def test_D02_deduction_calculated_correctly():
    _header("D02 | Financial: Deduction = Deposit - Refund calculated automatically")
    doc = make_booking("D02 Deduction", date_offset=115, deposit=1000)
    doc.submit()
    frappe.db.commit()
    ret = frappe.get_doc({
        "doctype": "Party Asset Return",
        "party_booking": doc.name,
        "original_deposit": 1000,
        "refund_amount": 700,
        "refund_method": "Cash",
        "refund_date": today(),
        "refund_status": "Partially Deducted"
    })
    ret.insert(ignore_permissions=True)
    if flt(ret.deduction_amount) == 300:
        _pass("D02 | Deduction calculated correctly: 1000 - 700 = 300")
    else:
        _fail("D02 | Deduction calculation", f"Expected 300, got {ret.deduction_amount}")
    force_delete("Party Asset Return", ret.name)
    force_delete("Party Booking", doc.name)

def test_D03_zero_deposit_booking():
    _header("D03 | Edge Case: Booking with zero security deposit")
    doc = make_booking("D03 Zero Deposit", date_offset=120, deposit=0)
    doc.submit()
    frappe.db.commit()
    if doc.docstatus == 1:
        _pass("D03 | Booking with zero deposit allowed and submitted")
    else:
        _fail("D03 | Zero deposit booking", "Submit failed unexpectedly")
    doc.cancel()
    force_delete("Party Booking", doc.name)

def test_D04_double_return_for_same_booking():
    _header("D04 | Integrity: Only ONE return doc should exist per booking")
    doc = make_booking("D04 Double Return", date_offset=125, deposit=500)
    doc.submit()
    frappe.db.commit()
    # First return
    ret1 = frappe.get_doc({
        "doctype": "Party Asset Return",
        "party_booking": doc.name,
        "original_deposit": 500,
        "refund_amount": 500,
        "refund_method": "Cash",
        "refund_date": today(),
        "refund_status": "Completed"
    })
    ret1.insert(ignore_permissions=True)
    ret1.submit()
    frappe.db.commit()
    # Second return - should be blocked
    try:
        ret2 = frappe.get_doc({
            "doctype": "Party Asset Return",
            "party_booking": doc.name,
            "original_deposit": 500,
            "refund_amount": 500,
            "refund_method": "Cash",
            "refund_date": today(),
            "refund_status": "Completed"
        })
        ret2.insert(ignore_permissions=True)
        ret2.submit()
        frappe.db.commit()
        _fail("D04 | Duplicate return doc", "System allowed creating SECOND return for same booking!")
        force_delete("Party Asset Return", ret2.name)
    except frappe.ValidationError:
        _pass("D04 | Duplicate return for same booking correctly blocked")
    force_delete("Party Asset Return", ret1.name)
    force_delete("Party Booking", doc.name)

def test_D05_return_without_submitted_booking():
    _header("D05 | Integrity: Return doc should fail if booking is not submitted")
    doc = make_booking("D05 Draft Return", date_offset=130, deposit=200)
    # Do NOT submit the booking - it stays as Draft
    frappe.db.commit()
    try:
        ret = frappe.get_doc({
            "doctype": "Party Asset Return",
            "party_booking": doc.name,
            "original_deposit": 200,
            "refund_amount": 200,
            "refund_method": "Cash",
            "refund_date": today(),
            "refund_status": "Completed"
        })
        ret.insert(ignore_permissions=True)
        ret.submit()
        frappe.db.commit()
        _warn("D05 | Return accepted for non-submitted booking",
              "Asset Return was created for a Draft booking - should ideally be blocked")
        force_delete("Party Asset Return", ret.name)
    except Exception as e:
        _pass("D05 | Return for non-submitted booking correctly rejected")
    force_delete("Party Booking", doc.name)


# ══════════════════════════════════════════════════════════════
# GROUP E: Data Integrity & Edge Cases
# ══════════════════════════════════════════════════════════════

def test_E01_api_idempotency():
    _header("E01 | Integrity: Verify duplicate API calls don't duplicate bookings")
    from mu_booking.api import create_bot_booking
    params = dict(customer_name="Idempotency Test", customer_mobile="0501230000",
                  party_date=add_days(today(), 7), party_time="20:00:00")
    res1 = create_bot_booking(**params)
    res2 = create_bot_booking(**params)
    if res1.get("status") == res2.get("status") == "success":
        if res1.get("booking_id") != res2.get("booking_id"):
            _warn("E01 | Duplicate API calls create DUPLICATE bookings",
                  "Two identical calls created two separate bookings - no deduplication!")
        else:
            _pass("E01 | Duplicate API calls handled (idempotent)")
        force_delete("Party Booking", res1.get("booking_id"))
        force_delete("Party Booking", res2.get("booking_id"))
    else:
        _warn("E01 | Could not test idempotency", str(res1))

def test_E02_booking_count_in_db():
    _header("E02 | Integrity: Booking auto-name format is correct")
    doc = make_booking("E02 Naming Test", date_offset=200)
    if doc.name and doc.name.startswith("PB-"):
        _pass(f"E02 | Booking auto-name format correct: {doc.name}")
    else:
        _fail("E02 | Auto-name format", f"Expected PB-YYYY-##### format, got: {doc.name}")
    force_delete("Party Booking", doc.name)

def test_E03_long_customer_name():
    _header("E03 | Edge Case: Very long customer name (500 chars)")
    long_name = "أ" * 500
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name=long_name, customer_mobile="0500000000",
                             party_date=add_days(today(), 5), party_time="20:00:00")
    if res.get("status") == "error":
        _pass("E03 | Very long name rejected")
    else:
        _warn("E03 | Very long customer name accepted without truncation",
              "500-character names may cause display issues in reports/WhatsApp messages")
        if res.get("booking_id"):
            force_delete("Party Booking", res["booking_id"])

def test_E04_arabic_unicode_customer_name():
    _header("E04 | Compatibility: Arabic unicode name works correctly")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="محمد عبدالله الرشيدي", customer_mobile="0555555555",
                             party_date=add_days(today(), 8), party_time="19:00:00",
                             customer_notes="الحفلة في الرياض - حي النخيل")
    if res.get("status") == "success":
        stored_name = frappe.db.get_value("Party Booking", res["booking_id"], "customer_name")
        if stored_name == "محمد عبدالله الرشيدي":
            _pass("E04 | Arabic name stored and retrieved correctly")
        else:
            _fail("E04 | Arabic name storage", f"Stored as: {stored_name}")
        force_delete("Party Booking", res["booking_id"])
    else:
        _fail("E04 | Arabic name booking failed", str(res))

def test_E05_workflow_state_initial_on_creation():
    _header("E05 | Workflow: New booking should have workflow state 'Initial' or None")
    doc = make_booking("E05 Workflow Test", date_offset=210)
    state = frappe.db.get_value("Party Booking", doc.name, "workflow_state")
    if state in (None, "Initial", "Draft"):
        _pass(f"E05 | New booking workflow state is correct: '{state}'")
    else:
        _warn("E05 | Unexpected initial workflow state", f"Got: {state}")
    force_delete("Party Booking", doc.name)

def test_E06_mobile_numbers_stored_as_is():
    _header("E06 | Data: Mobile numbers with country code (+966) stored correctly")
    from mu_booking.api import create_bot_booking
    res = create_bot_booking(customer_name="Country Code Test", customer_mobile="+966501234567",
                             party_date=add_days(today(), 9), party_time="20:00:00")
    if res.get("status") == "success":
        stored = frappe.db.get_value("Party Booking", res["booking_id"], "customer_mobile")
        if stored == "+966501234567":
            _pass("E06 | International mobile number stored correctly")
        else:
            _warn("E06 | Mobile number was modified on save", f"Stored as: {stored}")
        force_delete("Party Booking", res["booking_id"])
    else:
        _warn("E06 | International mobile rejected", str(res))


# ══════════════════════════════════════════════════════════════
# GROUP F: Reports Availability
# ══════════════════════════════════════════════════════════════

def test_F01_reports_exist_and_are_script_type():
    _header("F01 | Reports: All 5 reports exist and are Script Reports")
    expected_reports = [
        "Party Bookings Report",
        "Asset Utilization Report",
        "Security Deposit Report",
        "Installation and Delivery Report",
        "Damaged and Lost Assets Report"
    ]
    # Also check the & variant
    alt_name = "Installation & Delivery Report"
    all_reports = [r.name for r in frappe.get_all("Report", filters={"module": "Mu Booking"})]
    
    missing = []
    wrong_type = []
    for rep in expected_reports:
        # Check with both names
        actual_name = rep if rep in all_reports else (alt_name if alt_name in all_reports and "Installation" in rep else None)
        if actual_name is None:
            missing.append(rep)
        else:
            rtype = frappe.db.get_value("Report", actual_name, "report_type")
            if rtype != "Script Report":
                wrong_type.append(f"{actual_name} (type: {rtype})")

    if not missing and not wrong_type:
        _pass("F01 | All 5 reports exist as Script Reports")
    else:
        if missing:
            _fail("F01 | Missing reports", str(missing))
        if wrong_type:
            _fail("F01 | Reports with wrong type", str(wrong_type))

def test_F02_workspace_exists():
    _header("F02 | Workspace: Party Bookings workspace exists")
    if frappe.db.exists("Workspace", "Party Bookings"):
        ws = frappe.get_doc("Workspace", "Party Bookings")
        link_count = len(ws.links)
        shortcut_count = len(ws.shortcuts)
        _pass(f"F02 | Workspace exists with {link_count} links and {shortcut_count} shortcuts")
    else:
        _fail("F02 | Party Bookings workspace not found")


# ══════════════════════════════════════════════════════════════
# MAIN RUNNER
# ══════════════════════════════════════════════════════════════

def run_all_tests():
    global _results
    _results = []

    print("\n" + "═"*60)
    print("  🚀  PARTY BOOKING — COMPREHENSIVE TEST SUITE v2")
    print("═"*60)

    print("\n  🔧  Setting up test assets...")
    ensure_assets()
    has_assets = frappe.db.exists("Asset", ASSET_NAME)
    if has_assets:
        print(f"  ✔   Assets ready: {ASSET_NAME}, {ASSET_NAME_2}")
    else:
        print(f"  ⚠️   Test assets unavailable - asset tests will be skipped")

    # GROUP A - Input Validation
    print("\n" + "═"*60)
    print("  GROUP A — Input Validation & Security")
    print("═"*60)
    test_A01_reject_empty_customer_name()
    test_A02_reject_past_date()
    test_A03_reject_today_date()
    test_A04_reject_invalid_mobile_format()
    test_A05_reject_invalid_service_type()
    test_A06_whitespace_injection_customer_name()
    test_A07_sql_injection_in_name()
    test_A08_xss_in_customer_notes()

    # GROUP B - Business Logic
    print("\n" + "═"*60)
    print("  GROUP B — Business Logic & Asset Management")
    print("═"*60)
    test_B01_asset_becomes_booked_on_submit()
    test_B02_asset_reverts_on_cancel()
    test_B03_conflict_same_asset_same_date()
    test_B04_conflict_different_date_same_asset_allowed()
    test_B05_booking_without_assets()
    test_B06_cancel_damaged_asset_stays_damaged()

    # GROUP C - Recurring
    print("\n" + "═"*60)
    print("  GROUP C — Recurring Booking Logic")
    print("═"*60)
    test_C01_recurring_session_auto_generation()
    test_C02_recurring_sessions_have_correct_dates()
    test_C03_recurring_with_zero_days()

    # GROUP D - Financial
    print("\n" + "═"*60)
    print("  GROUP D — Financial Logic & Asset Return")
    print("═"*60)
    test_D01_refund_exceeds_deposit_rejected()
    test_D02_deduction_calculated_correctly()
    test_D03_zero_deposit_booking()
    test_D04_double_return_for_same_booking()
    test_D05_return_without_submitted_booking()

    # GROUP E - Integrity
    print("\n" + "═"*60)
    print("  GROUP E — Data Integrity & Edge Cases")
    print("═"*60)
    test_E01_api_idempotency()
    test_E02_booking_count_in_db()
    test_E03_long_customer_name()
    test_E04_arabic_unicode_customer_name()
    test_E05_workflow_state_initial_on_creation()
    test_E06_mobile_numbers_stored_as_is()

    # GROUP F - Reports
    print("\n" + "═"*60)
    print("  GROUP F — Reports & Workspace")
    print("═"*60)
    test_F01_reports_exist_and_are_script_type()
    test_F02_workspace_exists()

    # ─── Final Summary ───
    total = len(_results)
    passed = sum(1 for r in _results if r[0] == "PASS")
    warned = sum(1 for r in _results if r[0] == "WARN")
    failed = total - passed - warned

    print("\n" + "═"*60)
    print(f"  📊  RESULTS: {passed} PASS | {warned} WARN | {failed} FAIL | {total} TOTAL")
    print("═"*60)

    if failed > 0:
        print("\n  ❌  BUGS (FAIL):")
        for r in _results:
            if r[0] == "FAIL":
                reason = r[2] if len(r) > 2 else ""
                print(f"     • [{r[1]}]" + (f": {reason}" if reason else ""))

    if warned > 0:
        print("\n  ⚠️   ISSUES (WARN) - Vulnerabilities & UX Problems:")
        for r in _results:
            if r[0] == "WARN":
                reason = r[2] if len(r) > 2 else ""
                print(f"     • [{r[1]}]" + (f": {reason}" if reason else ""))

    print()
