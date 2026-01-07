from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Dashboard
    path('', views.bookings_dashboard, name='dashboard'),

    # Emplacements
    path('locations/', views.location_list, name='location_list'),
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:pk>/update/', views.location_update, name='location_update'),
    path('locations/<int:pk>/delete/', views.location_delete, name='location_delete'),

    # Tables
    path('tables/', views.table_list, name='table_list'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/<int:pk>/update/', views.table_update, name='table_update'),
    path('tables/<int:pk>/delete/', views.table_delete, name='table_delete'),

    # Réservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/quick-create/', views.reservation_quick_create, name='reservation_quick_create'),
    path('reservations/<int:pk>/update/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),
    path('reservations/<int:pk>/confirm/', views.reservation_confirm, name='reservation_confirm'),
    path('reservations/<int:pk>/cancel/', views.reservation_cancel, name='reservation_cancel'),
    path('reservations/<int:pk>/complete/', views.reservation_complete, name='reservation_complete'),
    path('reservations/<int:pk>/no-show/', views.reservation_no_show, name='reservation_no_show'),

    # Planning
    path('calendar/', views.reservation_calendar, name='reservation_calendar'),

    # Rapports
    path('reports/', views.bookings_reports, name='reports'),
]