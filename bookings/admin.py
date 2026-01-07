from django.contrib import admin
from .models import (
    TableLocation, Table, Reservation,
    ReservationHistory, TimeSlotAvailability
)


@admin.register(TableLocation)
class TableLocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_table_count', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ['table_number', 'location', 'capacity', 'is_available']
    list_filter = ['location', 'is_available', 'capacity']
    search_fields = ['table_number']


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'reservation_number', 'customer_name', 'customer_phone',
        'reservation_date', 'time_slot', 'number_of_guests',
        'table', 'status', 'created_at'
    ]
    list_filter = ['status', 'reservation_date', 'time_slot']
    search_fields = ['reservation_number', 'customer_name', 'customer_phone', 'customer_email']
    date_hierarchy = 'reservation_date'

    fieldsets = (
        ('Informations client', {
            'fields': ('customer_name', 'customer_phone', 'customer_email')
        }),
        ('Détails réservation', {
            'fields': (
                'reservation_number', 'reservation_date', 'time_slot',
                'number_of_guests', 'table', 'status'
            )
        }),
        ('Demandes spéciales', {
            'fields': ('special_requests', 'notes')
        }),
        ('Traçabilité', {
            'fields': ('created_by', 'confirmed_by', 'confirmed_at')
        }),
    )


@admin.register(ReservationHistory)
class ReservationHistoryAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['reservation__reservation_number']
    date_hierarchy = 'performed_at'


@admin.register(TimeSlotAvailability)
class TimeSlotAvailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'time_slot', 'max_reservations',
        'get_current_reservations', 'is_available'
    ]
    list_filter = ['date', 'time_slot', 'is_available']
    date_hierarchy = 'date'