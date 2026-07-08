import frappe

def execute():
    doc = frappe.get_doc("DocType", "Party Booking")
    
    # Update depends_on for existing fields
    for field in doc.fields:
        if field.fieldname == "start_date":
            field.depends_on = "eval:in_list(['Daily', 'Weekly', 'Monthly'], doc.recurring_pattern)"
        elif field.fieldname == "end_date":
            field.depends_on = "eval:in_list(['Weekly', 'Monthly'], doc.recurring_pattern)"
        elif field.fieldname == "number_of_days":
            field.depends_on = "eval:doc.recurring_pattern=='Daily'"
            
    new_fields_data = [
        {
            "fieldname": "weekly_section",
            "fieldtype": "Section Break",
            "label": "Weekly Details",
            "depends_on": "eval:doc.recurring_pattern=='Weekly'"
        },
        {"fieldname": "saturday", "fieldtype": "Check", "label": "Saturday"},
        {"fieldname": "sunday", "fieldtype": "Check", "label": "Sunday"},
        {"fieldname": "monday", "fieldtype": "Check", "label": "Monday"},
        {"fieldname": "cb_weekly_1", "fieldtype": "Column Break"},
        {"fieldname": "tuesday", "fieldtype": "Check", "label": "Tuesday"},
        {"fieldname": "wednesday", "fieldtype": "Check", "label": "Wednesday"},
        {"fieldname": "cb_weekly_2", "fieldtype": "Column Break"},
        {"fieldname": "thursday", "fieldtype": "Check", "label": "Thursday"},
        {"fieldname": "friday", "fieldtype": "Check", "label": "Friday"},
        {
            "fieldname": "monthly_section",
            "fieldtype": "Section Break",
            "label": "Monthly Details",
            "depends_on": "eval:doc.recurring_pattern=='Monthly'"
        },
        {"fieldname": "monthly_week", "fieldtype": "Select", "label": "Week of the Month", "options": "1st\n2nd\n3rd\n4th\nLast"},
        {"fieldname": "cb_monthly", "fieldtype": "Column Break"},
        {"fieldname": "monthly_day", "fieldtype": "Select", "label": "Day of the Week", "options": "Saturday\nSunday\nMonday\nTuesday\nWednesday\nThursday\nFriday"}
    ]
    
    # Find index of number_of_days
    insert_idx = -1
    for i, field in enumerate(doc.fields):
        if field.fieldname == "number_of_days":
            insert_idx = i
            break
            
    if insert_idx == -1:
        print("Could not find number_of_days field")
        return
        
    # Check if already added
    existing_fieldnames = [f.fieldname for f in doc.fields]
    if "saturday" in existing_fieldnames:
        print("Fields already exist!")
        # just save in case depends_on changed
        doc.save()
        return

    # Create new field objects
    for i, fd in enumerate(new_fields_data):
        new_row = doc.append("fields", {})
        new_row.update(fd)
        
    # Re-order the fields array to place them after number_of_days
    # The last len(new_fields_data) fields are the ones we just added
    num_new = len(new_fields_data)
    original_fields = doc.fields[:-num_new]
    added_fields = doc.fields[-num_new:]
    
    doc.fields = original_fields[:insert_idx+1] + added_fields + original_fields[insert_idx+1:]
    
    # Re-assign idx
    for i, f in enumerate(doc.fields):
        f.idx = i + 1
        
    doc.save()
    print("Schema updated successfully!")
