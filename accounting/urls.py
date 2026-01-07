from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('', views.accounting_dashboard, name='dashboard'),

    # Catégories de comptes
    path('categories/', views.account_category_list, name='account_category_list'),
    path('categories/create/', views.account_category_create, name='account_category_create'),
    path('categories/<int:pk>/update/', views.account_category_update, name='account_category_update'),
    path('categories/<int:pk>/delete/', views.account_category_delete, name='account_category_delete'),

    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/update/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),

    # Factures
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/create/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/update/', views.invoice_update, name='invoice_update'),
    path('invoices/<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('invoices/<int:pk>/add-item/', views.invoice_add_item, name='invoice_add_item'),
    path('invoice-items/<int:pk>/delete/', views.invoice_item_delete, name='invoice_item_delete'),
    path('invoices/<int:pk>/add-payment/', views.invoice_add_payment, name='invoice_add_payment'),

    # Rapports
    path('reports/', views.accounting_reports, name='reports'),
]