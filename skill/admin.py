# yourapp/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

#admin.site.register(CustomUser, UserAdmin)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_staff')  # Show user_type in admin list
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('user_type',)}),  # Add user_type to edit form
    )

admin.site.register(CustomUser, CustomUserAdmin)