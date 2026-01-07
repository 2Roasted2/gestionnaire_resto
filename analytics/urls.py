from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboard principal
    path('', views.analytics_dashboard, name='dashboard'),

    # Rapports détaillés
    path('financial/', views.financial_reports, name='financial_reports'),
    path('hr/', views.hr_reports, name='hr_reports'),
    path('inventory/', views.inventory_reports, name='inventory_reports'),
    path('reservations/', views.reservations_reports, name='reservations_reports'),
    path('sales/', views.sales_reports, name='sales_reports'),
]