from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from personnel.models import Employee, Attendance, Leave, Payroll
from inventory.models import Product, StockMovement
from accounting.models import Transaction, Invoice
from bookings.models import Reservation
from orders.models import Order, OrderItem


# Décorateur pour vérifier les permissions
def can_view_analytics(user):
    return user.is_authenticated and user.role in ['ADMIN', 'MANAGER']


# ==================== DASHBOARD EXÉCUTIF ====================
@login_required
@user_passes_test(can_view_analytics)
def analytics_dashboard(request):
    """Tableau de bord exécutif avec KPIs globaux"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    this_year_start = today.replace(month=1, day=1)

    # ========== FINANCES ==========
    # Revenus du mois
    monthly_revenue = Transaction.objects.filter(
        transaction_type='INCOME',
        date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Dépenses du mois
    monthly_expenses = Transaction.objects.filter(
        transaction_type='EXPENSE',
        date__gte=this_month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Balance du mois
    monthly_balance = monthly_revenue - monthly_expenses

    # Revenus année
    yearly_revenue = Transaction.objects.filter(
        transaction_type='INCOME',
        date__gte=this_year_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Factures impayées
    unpaid_invoices = Invoice.objects.filter(
        status__in=['SENT', 'OVERDUE', 'PARTIALLY_PAID']
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # ========== RESSOURCES HUMAINES ==========
    # Employés actifs
    active_employees = Employee.objects.filter(is_active=True).count()

    # Présences aujourd'hui
    today_attendance = Attendance.objects.filter(
        date=today,
        status='PRESENT'
    ).count()

    # Congés en cours
    active_leaves = Leave.objects.filter(
        status='APPROVED',
        start_date__lte=today,
        end_date__gte=today
    ).count()

    # Masse salariale du mois
    monthly_payroll = Payroll.objects.filter(
        month=today.month,
        year=today.year
    ).aggregate(total=Sum('net_salary'))['total'] or 0

    # ========== STOCK ==========
    # Valeur totale du stock - CORRECTION: quantity_in_stock au lieu de current_stock
    stock_value = Product.objects.aggregate(
        total=Sum(F('quantity_in_stock') * F('unit_price'))
    )['total'] or 0

    # Produits en alerte - CORRECTION: quantity_in_stock au lieu de current_stock
    products_low_stock = Product.objects.filter(
        quantity_in_stock__lte=F('minimum_stock')
    ).count()

    # Mouvements du mois
    monthly_stock_movements = StockMovement.objects.filter(
        created_at__date__gte=this_month_start
    ).count()

    # ========== RÉSERVATIONS ==========
    # Réservations du mois
    monthly_reservations = Reservation.objects.filter(
        reservation_date__gte=this_month_start
    ).count()

    # Réservations aujourd'hui
    today_reservations = Reservation.objects.filter(
        reservation_date=today
    ).count()

    # Taux de confirmation
    total_reservations_month = Reservation.objects.filter(
        reservation_date__gte=this_month_start
    ).count()
    confirmed_reservations = Reservation.objects.filter(
        reservation_date__gte=this_month_start,
        status='CONFIRMED'
    ).count()
    confirmation_rate = (confirmed_reservations / total_reservations_month * 100) if total_reservations_month > 0 else 0

    # ========== COMMANDES ==========
    # Commandes du mois
    monthly_orders = Order.objects.filter(
        order_date__date__gte=this_month_start
    ).count()

    # Commandes aujourd'hui
    today_orders = Order.objects.filter(
        order_date__date=today
    ).count()

    # Revenus commandes payées du mois
    monthly_orders_revenue = Order.objects.filter(
        order_date__date__gte=this_month_start,
        status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Panier moyen
    avg_order_value = Order.objects.filter(
        order_date__date__gte=this_month_start,
        status='PAID'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0

    # ========== ÉVOLUTION MENSUELLE (6 derniers mois) ==========
    months_data = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        revenue = Transaction.objects.filter(
            transaction_type='INCOME',
            date__gte=month_start,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        expenses = Transaction.objects.filter(
            transaction_type='EXPENSE',
            date__gte=month_start,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        orders_count = Order.objects.filter(
            order_date__date__gte=month_start,
            order_date__date__lt=next_month,
            status='PAID'
        ).count()

        reservations_count = Reservation.objects.filter(
            reservation_date__gte=month_start,
            reservation_date__lt=next_month
        ).count()

        months_data.append({
            'month': month_start.strftime('%B'),
            'revenue': float(revenue),
            'expenses': float(expenses),
            'balance': float(revenue - expenses),
            'orders': orders_count,
            'reservations': reservations_count,
        })

    # ========== TOP PLATS ==========
    top_items = OrderItem.objects.filter(
        order__order_date__date__gte=this_month_start,
        order__status='PAID'
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:5]

    context = {
        # Finances
        'monthly_revenue': monthly_revenue,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'yearly_revenue': yearly_revenue,
        'unpaid_invoices': unpaid_invoices,

        # RH
        'active_employees': active_employees,
        'today_attendance': today_attendance,
        'active_leaves': active_leaves,
        'monthly_payroll': monthly_payroll,

        # Stock
        'stock_value': stock_value,
        'products_low_stock': products_low_stock,
        'monthly_stock_movements': monthly_stock_movements,

        # Réservations
        'monthly_reservations': monthly_reservations,
        'today_reservations': today_reservations,
        'confirmation_rate': confirmation_rate,

        # Commandes
        'monthly_orders': monthly_orders,
        'today_orders': today_orders,
        'monthly_orders_revenue': monthly_orders_revenue,
        'avg_order_value': avg_order_value,

        # Données évolution
        'months_data': months_data,
        'top_items': top_items,
    }

    return render(request, 'analytics/dashboard.html', context)


# ==================== RAPPORTS FINANCIERS ====================
@login_required
@user_passes_test(can_view_analytics)
def financial_reports(request):
    """Rapports financiers détaillés"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    this_year_start = today.replace(month=1, day=1)

    # Revenus et dépenses par catégorie (année)
    revenue_by_category = Transaction.objects.filter(
        transaction_type='INCOME',
        date__gte=this_year_start
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    expense_by_category = Transaction.objects.filter(
        transaction_type='EXPENSE',
        date__gte=this_year_start
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Évolution mensuelle détaillée (12 derniers mois)
    monthly_evolution = []
    for i in range(11, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        revenue = Transaction.objects.filter(
            transaction_type='INCOME',
            date__gte=month_start,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        expenses = Transaction.objects.filter(
            transaction_type='EXPENSE',
            date__gte=month_start,
            date__lt=next_month
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_evolution.append({
            'month': month_start.strftime('%B %Y'),
            'revenue': float(revenue),
            'expenses': float(expenses),
            'balance': float(revenue - expenses),
        })

    # Factures par statut
    invoices_by_status = Invoice.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('total_amount')
    )

    # Top clients (par montant de factures)
    top_customers = Invoice.objects.values('customer_name').annotate(
        total_amount=Sum('total_amount'),
        invoice_count=Count('id')
    ).order_by('-total_amount')[:10]

    context = {
        'revenue_by_category': revenue_by_category,
        'expense_by_category': expense_by_category,
        'monthly_evolution': monthly_evolution,
        'invoices_by_status': invoices_by_status,
        'top_customers': top_customers,
    }

    return render(request, 'analytics/financial_reports.html', context)


# ==================== RAPPORTS RH ====================
@login_required
@user_passes_test(can_view_analytics)
def hr_reports(request):
    """Rapports ressources humaines"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    # Employés par département
    employees_by_department = Employee.objects.filter(
        is_active=True
    ).values('department__name').annotate(
        count=Count('id')
    )

    # Employés par poste (via user.role)
    employees_by_position = Employee.objects.filter(
        is_active=True
    ).values('user__role').annotate(
        count=Count('id')
    )

    # Présences du mois
    attendance_stats = Attendance.objects.filter(
        date__gte=this_month_start
    ).values('status').annotate(
        count=Count('id')
    )

    # Congés par type
    leaves_by_type = Leave.objects.filter(
        start_date__gte=this_month_start
    ).values('leave_type').annotate(
        count=Count('id')
    )

    # Congés par statut
    leaves_by_status = Leave.objects.filter(
        start_date__gte=this_month_start
    ).values('status').annotate(
        count=Count('id')
    )

    # Masse salariale par département
    payroll_by_department = Payroll.objects.filter(
        month=today.month,
        year=today.year
    ).values('employee__department__name').annotate(
        total=Sum('net_salary')
    )

    # Évolution de la masse salariale (6 derniers mois)
    payroll_evolution = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)

        total = Payroll.objects.filter(
            month=month_date.month,
            year=month_date.year
        ).aggregate(total=Sum('net_salary'))['total'] or 0

        payroll_evolution.append({
            'month': month_date.strftime('%B %Y'),
            'total': float(total),
        })

    context = {
        'employees_by_department': employees_by_department,
        'employees_by_position': employees_by_position,
        'attendance_stats': attendance_stats,
        'leaves_by_type': leaves_by_type,
        'leaves_by_status': leaves_by_status,
        'payroll_by_department': payroll_by_department,
        'payroll_evolution': payroll_evolution,
    }

    return render(request, 'analytics/hr_reports.html', context)


# ==================== RAPPORTS STOCK ====================
@login_required
@user_passes_test(can_view_analytics)
def inventory_reports(request):
    """Rapports de stock et inventaire"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)

    # Valeur du stock par catégorie - CORRECTION: quantity_in_stock
    stock_by_category = Product.objects.values('category__name').annotate(
        total_value=Sum(F('quantity_in_stock') * F('unit_price')),
        product_count=Count('id')
    ).order_by('-total_value')

    # Produits en alerte - CORRECTION: quantity_in_stock
    low_stock_products = Product.objects.filter(
        quantity_in_stock__lte=F('minimum_stock')
    ).select_related('category')[:20]

    # Mouvements par type (mois)
    movements_by_type = StockMovement.objects.filter(
        created_at__date__gte=this_month_start
    ).values('movement_type').annotate(
        count=Count('id'),
        total_value=Sum(F('quantity') * F('unit_price'))
    )

    # Top produits utilisés
    top_used_products = StockMovement.objects.filter(
        created_at__date__gte=this_month_start,
        movement_type='OUT'
    ).values('product__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:10]

    # Évolution de la valeur du stock (6 derniers mois)
    stock_value_evolution = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)

        # Valeur actuelle du stock - CORRECTION: quantity_in_stock
        value = Product.objects.aggregate(
            total=Sum(F('quantity_in_stock') * F('unit_price'))
        )['total'] or 0

        stock_value_evolution.append({
            'month': month_start.strftime('%B %Y'),
            'value': float(value),
        })

    context = {
        'stock_by_category': stock_by_category,
        'low_stock_products': low_stock_products,
        'movements_by_type': movements_by_type,
        'top_used_products': top_used_products,
        'stock_value_evolution': stock_value_evolution,
    }

    return render(request, 'analytics/inventory_reports.html', context)


# ==================== RAPPORTS RÉSERVATIONS ====================
@login_required
@user_passes_test(can_view_analytics)
def reservations_reports(request):
    """Rapports de réservations"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)

    # Réservations par statut
    reservations_by_status = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago
    ).values('status').annotate(
        count=Count('id')
    )

    # Créneaux horaires populaires
    popular_time_slots = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status__in=['CONFIRMED', 'COMPLETED']
    ).values('time_slot').annotate(
        count=Count('id')
    ).order_by('-count')

    # Tables les plus réservées
    popular_tables = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status__in=['CONFIRMED', 'COMPLETED']
    ).values('table__table_number').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # Taux d'occupation par jour de la semaine
    reservations_by_weekday = []
    for day in range(7):
        count = Reservation.objects.filter(
            reservation_date__gte=thirty_days_ago,
            reservation_date__week_day=day + 2,
            status__in=['CONFIRMED', 'COMPLETED']
        ).count()

        day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        reservations_by_weekday.append({
            'day': day_names[day],
            'count': count
        })

    # Évolution mensuelle
    monthly_reservations = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month_start = month_date.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)

        count = Reservation.objects.filter(
            reservation_date__gte=month_start,
            reservation_date__lt=next_month
        ).count()

        confirmed = Reservation.objects.filter(
            reservation_date__gte=month_start,
            reservation_date__lt=next_month,
            status='CONFIRMED'
        ).count()

        monthly_reservations.append({
            'month': month_start.strftime('%B %Y'),
            'total': count,
            'confirmed': confirmed,
        })

    context = {
        'reservations_by_status': reservations_by_status,
        'popular_time_slots': popular_time_slots,
        'popular_tables': popular_tables,
        'reservations_by_weekday': reservations_by_weekday,
        'monthly_reservations': monthly_reservations,
    }

    return render(request, 'analytics/reservations_reports.html', context)


# ==================== RAPPORTS VENTES ====================
@login_required
@user_passes_test(can_view_analytics)
def sales_reports(request):
    """Rapports de ventes et commandes"""

    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)

    # Ventes par type de commande
    sales_by_type = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='PAID'
    ).values('order_type').annotate(
        count=Count('id'),
        total_revenue=Sum('total_amount')
    )

    # Top 20 plats vendus
    top_selling_items = OrderItem.objects.filter(
        order__order_date__date__gte=thirty_days_ago,
        order__status='PAID'
    ).values('menu_item__name', 'menu_item__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:20]

    # Ventes par catégorie de menu
    sales_by_category = OrderItem.objects.filter(
        order__order_date__date__gte=thirty_days_ago,
        order__status='PAID'
    ).values('menu_item__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_revenue')

    # Évolution quotidienne (7 derniers jours)
    daily_sales = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)

        revenue = Order.objects.filter(
            order_date__date=day,
            status='PAID'
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        orders_count = Order.objects.filter(
            order_date__date=day,
            status='PAID'
        ).count()

        daily_sales.append({
            'date': day.strftime('%d/%m'),
            'revenue': float(revenue),
            'orders': orders_count,
        })

    # Performances par serveur
    sales_by_waiter = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='PAID',
        served_by__isnull=False
    ).values('served_by__first_name', 'served_by__last_name').annotate(
        orders_count=Count('id'),
        total_revenue=Sum('total_amount')
    ).order_by('-total_revenue')[:10]

    context = {
        'sales_by_type': sales_by_type,
        'top_selling_items': top_selling_items,
        'sales_by_category': sales_by_category,
        'daily_sales': daily_sales,
        'sales_by_waiter': sales_by_waiter,
    }

    return render(request, 'analytics/sales_reports.html', context)