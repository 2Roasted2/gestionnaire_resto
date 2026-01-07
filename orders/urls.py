from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Dashboard
    path('', views.orders_dashboard, name='dashboard'),

    # Catégories de menu
    path('menu-categories/', views.menu_category_list, name='menu_category_list'),
    path('menu-categories/create/', views.menu_category_create, name='menu_category_create'),
    path('menu-categories/<int:pk>/update/', views.menu_category_update, name='menu_category_update'),
    path('menu-categories/<int:pk>/delete/', views.menu_category_delete, name='menu_category_delete'),

    # Plats du menu
    path('menu-items/', views.menu_item_list, name='menu_item_list'),
    path('menu-items/<int:pk>/', views.menu_item_detail, name='menu_item_detail'),
    path('menu-items/create/', views.menu_item_create, name='menu_item_create'),
    path('menu-items/<int:pk>/update/', views.menu_item_update, name='menu_item_update'),
    path('menu-items/<int:pk>/delete/', views.menu_item_delete, name='menu_item_delete'),
    path('menu-items/<int:pk>/add-ingredient/', views.menu_item_add_ingredient, name='menu_item_add_ingredient'),
    path('menu-item-ingredients/<int:pk>/delete/', views.menu_item_ingredient_delete,
         name='menu_item_ingredient_delete'),

    # Commandes
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/quick-create/', views.order_quick_create, name='order_quick_create'),
    path('orders/<int:pk>/add-items/', views.order_add_items, name='order_add_items'),
    path('order-items/<int:pk>/delete/', views.order_item_delete, name='order_item_delete'),
    path('orders/<int:pk>/confirm/', views.order_confirm, name='order_confirm'),
    path('orders/<int:pk>/mark-ready/', views.order_mark_ready, name='order_mark_ready'),
    path('orders/<int:pk>/mark-served/', views.order_mark_served, name='order_mark_served'),
    path('orders/<int:pk>/mark-paid/', views.order_mark_paid, name='order_mark_paid'),

    # Cuisine
    path('kitchen/', views.kitchen_display, name='kitchen_display'),
    path('kitchen-tickets/<int:pk>/start/', views.kitchen_ticket_start, name='kitchen_ticket_start'),
    path('kitchen-tickets/<int:pk>/complete/', views.kitchen_ticket_complete, name='kitchen_ticket_complete'),

    # Rapports
    path('reports/', views.orders_reports, name='reports'),
]