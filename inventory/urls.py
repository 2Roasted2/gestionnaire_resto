from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Dashboard
    path('', views.inventory_dashboard, name='dashboard'),

    # Catégories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Fournisseurs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),

    # Produits
    path('products/', views.product_list, name='product_list'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<int:pk>/update/', views.product_update, name='product_update'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),

    # Mouvements de stock
    path('stock-movements/', views.stock_movement_list, name='stock_movement_list'),
    path('stock-movements/create/', views.stock_movement_create, name='stock_movement_create'),
    path('stock-movements/<int:pk>/delete/', views.stock_movement_delete, name='stock_movement_delete'),

    # Bons de commande
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('purchase-orders/<int:pk>/add-item/', views.purchase_order_add_item, name='purchase_order_add_item'),
    path('purchase-order-items/<int:pk>/delete/', views.purchase_order_item_delete, name='purchase_order_item_delete'),
    path('purchase-orders/<int:pk>/receive/', views.purchase_order_receive, name='purchase_order_receive'),

    # Inventaires
    path('inventories/', views.inventory_list, name='inventory_list'),
    path('inventories/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('inventories/create/', views.inventory_create, name='inventory_create'),
    path('inventories/<int:pk>/update/', views.inventory_update, name='inventory_update'),
    path('inventories/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),
    path('inventories/<int:pk>/items/<int:item_pk>/update/', views.inventory_update_item, name='inventory_update_item'),
    path('inventories/<int:pk>/complete/', views.inventory_complete, name='inventory_complete'),

    # Rapports
    path('reports/', views.inventory_reports, name='reports'),
]