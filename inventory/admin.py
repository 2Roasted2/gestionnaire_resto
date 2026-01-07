from django.contrib import admin
from .models import (
    Category, Supplier, Product, StockMovement,
    PurchaseOrder, PurchaseOrderItem, Inventory, InventoryItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_product_count', 'created_at']
    search_fields = ['name']

    def get_product_count(self, obj):
        return obj.get_product_count()

    get_product_count.short_description = 'Nombre de produits'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'phone', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'contact_person', 'is_active')
        }),
        ('Contact', {
            'fields': ('email', 'phone', 'address', 'website')
        }),
        ('Informations commerciales', {
            'fields': ('tax_id', 'payment_terms')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'reference', 'name', 'category', 'supplier',
        'quantity_in_stock', 'unit', 'unit_price', 'stock_status', 'is_active'
    ]
    list_filter = ['category', 'supplier', 'unit', 'is_active']
    search_fields = ['reference', 'name', 'barcode']

    fieldsets = (
        ('Informations de base', {
            'fields': ('reference', 'name', 'category', 'supplier', 'description', 'image')
        }),
        ('Stock', {
            'fields': ('unit', 'quantity_in_stock', 'minimum_stock', 'optimal_stock')
        }),
        ('Prix', {
            'fields': ('unit_price',)
        }),
        ('Autres', {
            'fields': ('barcode', 'is_active')
        }),
    )


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['product', 'movement_type', 'quantity', 'unit_price', 'created_by', 'created_at']
    list_filter = ['movement_type', 'created_at']
    search_fields = ['product__name', 'reference', 'reason']
    date_hierarchy = 'created_at'

    def has_change_permission(self, request, obj=None):
        # Empêcher la modification des mouvements après création
        return False


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'received_quantity']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'supplier', 'order_date',
        'expected_delivery_date', 'status', 'total_amount'
    ]
    list_filter = ['status', 'order_date']
    search_fields = ['order_number', 'supplier__name']
    date_hierarchy = 'order_date'
    inlines = [PurchaseOrderItemInline]


class InventoryItemInline(admin.TabularInline):
    model = InventoryItem
    extra = 1
    fields = ['product', 'theoretical_quantity', 'physical_quantity', 'notes']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['inventory_number', 'inventory_date', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'inventory_date']
    search_fields = ['inventory_number']
    date_hierarchy = 'inventory_date'
    inlines = [InventoryItemInline]