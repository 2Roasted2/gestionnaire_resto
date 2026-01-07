from django.contrib import admin
from .models import (
    MenuCategory, MenuItem, MenuItemIngredient,
    Order, OrderItem, KitchenTicket
)

@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_order', 'get_menu_items_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    ordering = ['display_order', 'name']


class MenuItemIngredientInline(admin.TabularInline):
    model = MenuItemIngredient
    extra = 1


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'price', 'is_available',
        'is_vegetarian', 'is_vegan', 'track_inventory'
    ]
    list_filter = ['category', 'is_available', 'is_vegetarian', 'is_vegan']
    search_fields = ['name', 'description']
    inlines = [MenuItemIngredientInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'order_type', 'table', 'status',
        'total_amount', 'created_by', 'order_date'
    ]
    list_filter = ['status', 'order_type', 'order_date']
    search_fields = ['order_number', 'customer_name', 'customer_phone']
    date_hierarchy = 'order_date'
    inlines = [OrderItemInline]


@admin.register(KitchenTicket)
class KitchenTicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'order', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['ticket_number', 'order__order_number']