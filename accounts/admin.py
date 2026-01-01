from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_active', 'hire_date']
    list_filter = ['role', 'is_active', 'is_staff', 'hire_date']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'address', 'photo', 'date_of_birth', 'hire_date')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('role', 'phone', 'address', 'photo', 'date_of_birth')
        }),
    )