# yourapp/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

#admin.site.register(CustomUser, UserAdmin)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff')  # Show user_type in admin list
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type',)}),  # Add user_type to edit form
    )

admin.site.register(CustomUser, CustomUserAdmin)

class BookAppointmentAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'user', 'full_name', 'get_issue_display', 'status', 'payment_status', 'payout_status', 'expected_time', 'rating', 'created_at') # Added 'rating', 'payment_status', 'payout_status'
    list_filter = ('status', 'payment_status', 'payout_status', 'issue', 'created_at','otp_verified')
    search_fields = ('booking_id', 'full_name', 'contact_number', 'user__username')
    readonly_fields = ('booking_id', 'created_at')
    ordering = ('-created_at',)
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'user', 'status', 'created_at', 'rating') # Added 'rating'
        }),
        ('Payment & Payout Details', {
            'fields': ('payment_status', 'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'payout_status', 'payout_transaction_id')
        }),
        ('Customer Details', {
            'fields': ('full_name', 'contact_number')
        }),
        ('Service Information', {
            'fields': ('issue', 'custom_issue', 'description', 'expected_amount', 'expected_time','otp_verified')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'pincode')
        }),
        ('Images', {
            'fields': ('image1', 'image2', 'image3', 'image4'),
            'classes': ('collapse',)
        }),
    )

    def get_issue_display(self, obj):
        return obj.get_issue_domain()
    get_issue_display.short_description = 'Service Type'

admin.site.register(Book_Appointment, BookAppointmentAdmin)
admin.site.register(ServiceProviderDetails)
admin.site.register(ServiceProviderBankDetails)
admin.site.register(ServiceInitialRegistrationPayment)
admin.site.register(Bargaining)
admin.site.register(BargainingHistory)