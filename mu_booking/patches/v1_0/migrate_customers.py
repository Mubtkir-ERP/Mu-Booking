import frappe

def execute():
    """Migrate old Party Bookings to use the new Customer link field."""
    # Find all Party Bookings where customer is empty but customer_name is not
    bookings = frappe.db.sql("""
        SELECT name, customer_name, customer_mobile 
        FROM `tabParty Booking` 
        WHERE ifnull(customer, '') = '' AND ifnull(customer_name, '') != ''
    """, as_dict=True)

    for b in bookings:
        mobile = (b.customer_mobile or "0000000000").strip()
        customer_name = b.customer_name.strip()
        
        # Check if customer with this mobile exists
        customer_id = frappe.db.get_value("Customer", {"mobile_no": mobile}, "name")
        
        if not customer_id:
            try:
                new_cust = frappe.get_doc({
                    "doctype": "Customer",
                    "customer_name": customer_name,
                    "customer_group": "Commercial",
                    "territory": "All Territories",
                    "customer_type": "Individual",
                    "mobile_no": mobile
                })
                new_cust.insert(ignore_permissions=True)
                customer_id = new_cust.name
            except Exception as e:
                frappe.log_error(title="Customer Migration Error", message=f"Failed for booking {b.name}: {str(e)}")
                continue
                
        if customer_id:
            frappe.db.set_value("Party Booking", b.name, "customer", customer_id, update_modified=False)
            
    # Also fix Party Asset Return
    returns = frappe.db.sql("""
        SELECT par.name, pb.customer
        FROM `tabParty Asset Return` par
        JOIN `tabParty Booking` pb ON par.party_booking = pb.name
        WHERE ifnull(par.customer, '') = '' AND ifnull(pb.customer, '') != ''
    """, as_dict=True)
    
    for r in returns:
        frappe.db.set_value("Party Asset Return", r.name, "customer", r.customer, update_modified=False)
        
    frappe.db.commit()
