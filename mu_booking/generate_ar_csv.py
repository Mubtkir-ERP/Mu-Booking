import os
import csv
import frappe

def execute():
    app_path = frappe.get_app_path("mu_booking")
    translations_dir = os.path.join(app_path, "translations")
    
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)
        
    csv_file = os.path.join(translations_dir, "ar.csv")
    
    translations = {
        # Doctypes
        "Party Booking": "حجز حفلة",
        "Party Bookings": "حجوزات الحفلات",
        "Party Asset Return": "إرجاع أصول الحفلة",
        "Party Asset Returns": "إرجاعات أصول الحفلة",
        "Party Booking Asset": "أصل حجز الحفلة",
        "Party Booking Session": "جلسة حجز الحفلة",
        "Party Booking Reminder": "تذكير حجز الحفلة",
        "Event Type": "نوع المناسبة",
        "Event Types": "أنواع المناسبات",
        
        # Modules / Workspace
        "Mu Booking": "حجوزات مو",
        
        # Fields - Party Booking
        "Customer Information": "معلومات العميل",
        "Customer": "العميل",
        "Customer Name": "اسم العميل",
        "Customer Mobile": "جوال العميل",
        "Receiver Mobile": "جوال المستلم",
        "Party Location": "موقع الحفلة",
        "Location Link (Google Maps)": "رابط الموقع (خرائط جوجل)",
        "Customer Notes": "ملاحظات العميل",
        
        "Booking Information": "معلومات الحجز",
        "Service Type": "نوع الخدمة",
        "Booking Type": "نوع الحجز",
        "Party Date": "تاريخ الحفلة",
        "Party Time": "وقت الحفلة",
        "Booking Officer": "مسؤول الحجز",
        
        "Recurring Booking Details": "تفاصيل الحجز المتكرر",
        "Recurring Pattern": "نمط التكرار",
        "Start Date": "تاريخ البدء",
        "Number of Days/Sessions": "عدد الأيام/الجلسات",
        "End Date": "تاريخ الانتهاء",
        
        "Sessions": "الجلسات",
        "Booking Sessions": "جلسات الحجز",
        
        "Booking Assets": "أصول الحجز",
        "Assets": "الأصول",
        
        "Financial Information": "المعلومات المالية",
        "Security Deposit": "مبلغ التأمين",
        "Deposit Status": "حالة التأمين",
        "Invoice Reference": "المرجع للفاتورة",
        
        # Options
        "Delivery Only": "توصيل فقط",
        "Delivery and Installation": "توصيل وتركيب",
        "One-time": "لمرة واحدة",
        "Recurring": "متكرر",
        "Daily": "يومياً",
        "Weekly": "أسبوعياً",
        "Monthly": "شهرياً",
        "Manual": "يدوي",
        "Pending": "معلق",
        "Refunded": "تم الاسترجاع",
        "Partially Deducted": "مخصوم جزئياً",
        
        # Fields - Party Asset Return
        "Original Deposit": "التأمين الأصلي",
        "Refund Details": "تفاصيل الاسترجاع",
        "Refund Amount": "مبلغ الاسترجاع",
        "Deduction Amount": "مبلغ الخصم",
        "Deduction Reason": "سبب الخصم",
        "Refund Method": "طريقة الاسترجاع",
        "Payment Account": "حساب الدفع",
        "Refund Date": "تاريخ الاسترجاع",
        "Refund Status": "حالة الاسترجاع",
        "Accountant Notes": "ملاحظات المحاسب",
        "Notes": "الملاحظات",
        "Completed": "مكتمل",
        "Cash": "نقدي",
        "Bank Transfer": "تحويل بنكي",
        
        # Fields - Party Booking Asset
        "Asset": "الأصل",
        "Qty": "الكمية",
        "Serial No": "الرقم التسلسلي",
        "Asset Booking Status": "حالة حجز الأصل",
        "Condition on Delivery": "الحالة عند التسليم",
        "Condition on Return": "الحالة عند الإرجاع",
        "Available": "متاح",
        "Booked": "محجوز",
        "Damaged": "تالف",
        "Lost": "مفقود",
        
        # Fields - Party Booking Session
        "Session Date": "تاريخ الجلسة",
        "Session Time": "وقت الجلسة",
        "Session Status": "حالة الجلسة",
        "Cancellation Reason": "سبب الإلغاء",
        "Scheduled": "مجدول",
        "Cancelled": "ملغى",
        
        # Workflow States
        "Draft": "مسودة",
        "Submitted": "مقدم",
        "Approved": "معتمد",
        "Rejected": "مرفوض",
        "Confirmed": "مؤكد",
        "Delivery/Installation Scheduled": "تمت جدولة التوصيل/التركيب",
        "In Progress": "قيد التنفيذ",
        "Ready for Collection": "جاهز للاستلام",
        "Assets Returned": "تم إرجاع الأصول",
        "Closed": "مغلق",
        "Pending Return": "بانتظار الإرجاع",
        "Return Initiated": "بدء الإرجاع",
        
        # Reports
        "Asset Utilization Report": "تقرير استخدام الأصول",
        "Party Bookings Report": "تقرير حجوزات الحفلات",
        "Security Deposit Report": "تقرير مبالغ التأمين",
        "Damaged and Lost Assets Report": "تقرير الأصول التالفة والمفقودة",
        
        # API Messages
        "Customer name is required.": "اسم العميل مطلوب.",
        "Customer mobile is required.": "رقم جوال العميل مطلوب.",
        "Customer mobile must be a valid phone number.": "يجب أن يكون رقم الجوال صحيحاً.",
        "Party date is required.": "تاريخ الحفلة مطلوب.",
        "Party date cannot be in the past.": "لا يمكن أن يكون تاريخ الحفلة في الماضي.",
        "booking_type must be 'One-time' or 'Recurring'.": "نوع الحجز يجب أن يكون لمرة واحدة أو متكرر.",
        "Invalid service_type.": "نوع خدمة غير صالح.",
        "A booking already exists for this mobile number on the same date.": "يوجد حجز مسبق لهذا الرقم في نفس اليوم.",
        "Booking created successfully.": "تم إنشاء الحجز بنجاح."
    }
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for source, translated in translations.items():
            writer.writerow([source, translated])
            
    # Clear cache to apply translations
    frappe.clear_cache()
    
    return {"status": "success", "message": f"Translation file created at {csv_file} with {len(translations)} words!"}
