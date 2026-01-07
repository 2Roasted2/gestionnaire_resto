from django.contrib import admin
from .models import (
    AccountCategory, Transaction, Invoice, InvoiceItem,
    Payment, Budget
)

@admin.register(AccountCategory)
class AccountCategoryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'is_active']
    list_filter = ['account_type', 'is_active']
    search_fields = ['code', 'name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        'transaction_number', 'date', 'transaction_type',
        'category', 'amount', 'payment_method', 'created_by'
    ]
    list_filter = ['transaction_type', 'payment_method', 'date']
    search_fields = ['transaction_number', 'description', 'reference']
    date_hierarchy = 'date'


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'customer_name', 'issue_date',
        'due_date', 'total_amount', 'paid_amount', 'status'
    ]
    list_filter = ['status', 'issue_date']
    search_fields = ['invoice_number', 'customer_name', 'customer_email']
    date_hierarchy = 'issue_date'
    inlines = [InvoiceItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'invoice', 'payment_date',
        'amount', 'payment_method', 'created_by'
    ]
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['payment_number', 'reference']
    date_hierarchy = 'payment_date'


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        'category', 'period', 'year', 'month',
        'budgeted_amount', 'get_actual_amount', 'get_variance'
    ]
    list_filter = ['period', 'year', 'category']