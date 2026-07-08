import frappe

def fix_permissions():
    doctypes = ["Party Booking", "Party Asset Return"]
    
    roles_perms = [
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1},
        {"role": "Party Booking Officer", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1},
        {"role": "Party Installation Manager", "read": 1, "write": 1},
        {"role": "Party Accountant", "read": 1, "write": 1, "create": 1, "submit": 1, "cancel": 1}
    ]
    
    for dt in doctypes:
        if frappe.db.exists("DocType", dt):
            doc = frappe.get_doc("DocType", dt)
            doc.permissions = [] # Clear existing
            for rp in roles_perms:
                doc.append("permissions", rp)
            doc.save(ignore_permissions=True)
            print(f"Permissions updated for {dt}")

    # For child tables, they usually don't need explicit permissions if they are just child tables,
    # but we can add System Manager just in case, though it's optional for Table types.
    
    frappe.db.commit()
    print("All permissions fixed successfully.")
