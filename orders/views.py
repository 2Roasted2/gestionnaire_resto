from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta

from .models import (
    MenuCategory, MenuItem, MenuItemIngredient,
    Order, OrderItem, KitchenTicket
)
from .forms import (
    MenuCategoryForm, MenuItemForm, MenuItemIngredientForm,
    OrderForm, OrderItemForm, QuickOrderForm, OrderSearchForm
)


# Décorateur pour vérifier les permissions
def can_manage_orders(user):
    return user.is_authenticated and user.can_manage_orders()


# ==================== DASHBOARD ====================
@login_required
@user_passes_test(can_manage_orders)
def orders_dashboard(request):
    """Tableau de bord du module Commandes"""

    today = timezone.now().date()

    # Commandes du jour
    today_orders = Order.objects.filter(order_date__date=today).count()

    # Commandes en cours
    active_orders = Order.objects.filter(
        status__in=['PENDING', 'CONFIRMED', 'PREPARING']
    ).count()

    # Commandes prêtes
    ready_orders = Order.objects.filter(status='READY').count()

    # Revenus du jour
    today_revenue = Order.objects.filter(
        order_date__date=today,
        status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Commandes actives détaillées
    active_orders_list = Order.objects.filter(
        status__in=['PENDING', 'CONFIRMED', 'PREPARING', 'READY']
    ).select_related('table', 'created_by').order_by('order_date')[:10]

    # Tickets de cuisine en attente
    pending_tickets = KitchenTicket.objects.filter(
        status__in=['NEW', 'IN_PROGRESS']
    ).select_related('order').order_by('created_at')[:5]

    # Plats les plus vendus (7 derniers jours)
    top_items = OrderItem.objects.filter(
        order__order_date__gte=today - timedelta(days=7),
        order__status='PAID'
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity')
    ).order_by('-total_quantity')[:5]

    # Statistiques par type de commande
    orders_by_type = Order.objects.filter(
        order_date__date=today
    ).values('order_type').annotate(count=Count('id'))

    context = {
        'today_orders': today_orders,
        'active_orders': active_orders,
        'ready_orders': ready_orders,
        'today_revenue': today_revenue,
        'active_orders_list': active_orders_list,
        'pending_tickets': pending_tickets,
        'top_items': top_items,
        'orders_by_type': orders_by_type,
    }

    return render(request, 'orders/dashboard.html', context)


# ==================== CATÉGORIES DE MENU ====================
@login_required
@user_passes_test(can_manage_orders)
def menu_category_list(request):
    """Liste des catégories de menu"""
    categories = MenuCategory.objects.all()
    return render(request, 'orders/menu_category_list.html', {'categories': categories})


@login_required
@user_passes_test(can_manage_orders)
def menu_category_create(request):
    """Créer une catégorie de menu"""
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie créée avec succès.')
            return redirect('orders:menu_category_list')
    else:
        form = MenuCategoryForm()

    return render(request, 'orders/menu_category_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_orders)
def menu_category_update(request, pk):
    """Modifier une catégorie de menu"""
    category = get_object_or_404(MenuCategory, pk=pk)

    if request.method == 'POST':
        form = MenuCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie modifiée avec succès.')
            return redirect('orders:menu_category_list')
    else:
        form = MenuCategoryForm(instance=category)

    return render(request, 'orders/menu_category_form.html', {
        'form': form,
        'category': category,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_orders)
def menu_category_delete(request, pk):
    """Supprimer une catégorie de menu"""
    category = get_object_or_404(MenuCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Catégorie supprimée avec succès.')
        return redirect('orders:menu_category_list')

    return render(request, 'orders/menu_category_confirm_delete.html', {'category': category})


# ==================== PLATS DU MENU ====================
@login_required
@user_passes_test(can_manage_orders)
def menu_item_list(request):
    """Liste des plats du menu"""
    items = MenuItem.objects.select_related('category').all()
    return render(request, 'orders/menu_item_list.html', {'items': items})


@login_required
@user_passes_test(can_manage_orders)
def menu_item_detail(request, pk):
    """Détails d'un plat"""
    item = get_object_or_404(MenuItem, pk=pk)
    ingredients = item.ingredients.select_related('product').all()

    context = {
        'item': item,
        'ingredients': ingredients,
    }

    return render(request, 'orders/menu_item_detail.html', context)


@login_required
@user_passes_test(can_manage_orders)
def menu_item_create(request):
    """Créer un plat"""
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, 'Plat créé avec succès.')
            return redirect('orders:menu_item_detail', pk=item.pk)
    else:
        form = MenuItemForm()

    return render(request, 'orders/menu_item_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_orders)
def menu_item_update(request, pk):
    """Modifier un plat"""
    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plat modifié avec succès.')
            return redirect('orders:menu_item_detail', pk=item.pk)
    else:
        form = MenuItemForm(instance=item)

    return render(request, 'orders/menu_item_form.html', {
        'form': form,
        'item': item,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_orders)
def menu_item_delete(request, pk):
    """Supprimer un plat"""
    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Plat supprimé avec succès.')
        return redirect('orders:menu_item_list')

    return render(request, 'orders/menu_item_confirm_delete.html', {'item': item})


@login_required
@user_passes_test(can_manage_orders)
def menu_item_add_ingredient(request, pk):
    """Ajouter un ingrédient à un plat"""
    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == 'POST':
        form = MenuItemIngredientForm(request.POST)
        if form.is_valid():
            ingredient = form.save(commit=False)
            ingredient.menu_item = item
            ingredient.save()
            messages.success(request, 'Ingrédient ajouté avec succès.')
            return redirect('orders:menu_item_detail', pk=item.pk)
    else:
        form = MenuItemIngredientForm()

    ingredients = item.ingredients.select_related('product').all()

    return render(request, 'orders/menu_item_add_ingredient.html', {
        'form': form,
        'item': item,
        'ingredients': ingredients,
    })


@login_required
@user_passes_test(can_manage_orders)
def menu_item_ingredient_delete(request, pk):
    """Supprimer un ingrédient d'un plat"""
    ingredient = get_object_or_404(MenuItemIngredient, pk=pk)
    item = ingredient.menu_item

    if request.method == 'POST':
        ingredient.delete()
        messages.success(request, 'Ingrédient supprimé avec succès.')
        return redirect('orders:menu_item_detail', pk=item.pk)

    return render(request, 'orders/menu_item_ingredient_confirm_delete.html', {
        'ingredient': ingredient,
        'item': item
    })


# ==================== COMMANDES ====================
@login_required
@user_passes_test(can_manage_orders)
def order_list(request):
    """Liste des commandes avec recherche et filtres"""
    orders = Order.objects.select_related('table', 'created_by', 'served_by').all()

    # Formulaire de recherche
    search_form = OrderSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        order_type = search_form.cleaned_data.get('order_type')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')

        if search_query:
            orders = orders.filter(
                Q(order_number__icontains=search_query) |
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query)
            )

        if status:
            orders = orders.filter(status=status)

        if order_type:
            orders = orders.filter(order_type=order_type)

        if date_from:
            orders = orders.filter(order_date__date__gte=date_from)

        if date_to:
            orders = orders.filter(order_date__date__lte=date_to)

    context = {
        'orders': orders,
        'search_form': search_form,
    }

    return render(request, 'orders/order_list.html', context)


@login_required
@user_passes_test(can_manage_orders)
def order_detail(request, pk):
    """Détails d'une commande"""
    order = get_object_or_404(Order, pk=pk)
    items = order.items.select_related('menu_item').all()

    context = {
        'order': order,
        'items': items,
    }

    return render(request, 'orders/order_detail.html', context)


@login_required
@user_passes_test(can_manage_orders)
def order_create(request):
    """Créer une commande"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()

            messages.success(request, f'Commande {order.order_number} créée avec succès.')
            return redirect('orders:order_add_items', pk=order.pk)
    else:
        # Générer un numéro de commande automatique
        order_number = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = OrderForm(initial={
            'order_number': order_number,
            'tax_rate': 10
        })

    return render(request, 'orders/order_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_orders)
def order_quick_create(request):
    """Prise de commande rapide"""
    if request.method == 'POST':
        form = QuickOrderForm(request.POST)
        if form.is_valid():
            order_number = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            order = Order.objects.create(
                order_number=order_number,
                order_type=form.cleaned_data['order_type'],
                table=form.cleaned_data.get('table'),
                customer_name=form.cleaned_data.get('customer_name', ''),
                created_by=request.user
            )

            messages.success(request, f'Commande {order.order_number} créée avec succès.')
            return redirect('orders:order_add_items', pk=order.pk)
    else:
        form = QuickOrderForm()

    return render(request, 'orders/order_quick_form.html', {'form': form})


@login_required
@user_passes_test(can_manage_orders)
def order_add_items(request, pk):
    """Ajouter des articles à une commande"""
    order = get_object_or_404(Order, pk=pk)

    if request.method == 'POST':
        form = OrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.order = order
            item.unit_price = item.menu_item.price
            item.save()

            # Recalculer les totaux
            order.calculate_totals()
            order.save()

            messages.success(request, 'Article ajouté avec succès.')
            return redirect('orders:order_add_items', pk=order.pk)
    else:
        form = OrderItemForm()

    items = order.items.select_related('menu_item').all()
    menu_categories = MenuCategory.objects.filter(is_active=True).prefetch_related('menu_items')

    context = {
        'form': form,
        'order': order,
        'items': items,
        'menu_categories': menu_categories,
    }

    return render(request, 'orders/order_add_items.html', context)


@login_required
@user_passes_test(can_manage_orders)
def order_item_delete(request, pk):
    """Supprimer un article d'une commande"""
    item = get_object_or_404(OrderItem, pk=pk)
    order = item.order

    if request.method == 'POST':
        item.delete()

        # Recalculer les totaux
        order.calculate_totals()
        order.save()

        messages.success(request, 'Article supprimé avec succès.')
        return redirect('orders:order_add_items', pk=order.pk)

    return render(request, 'orders/order_item_confirm_delete.html', {
        'item': item,
        'order': order
    })


@login_required
@user_passes_test(can_manage_orders)
def order_confirm(request, pk):
    """Confirmer une commande"""
    order = get_object_or_404(Order, pk=pk)

    order.mark_confirmed()

    # Créer un ticket de cuisine
    ticket_number = f"KT-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    KitchenTicket.objects.create(
        order=order,
        ticket_number=ticket_number
    )

    messages.success(request, f'Commande {order.order_number} confirmée et envoyée en cuisine.')
    return redirect('orders:order_detail', pk=order.pk)


@login_required
@user_passes_test(can_manage_orders)
def order_mark_ready(request, pk):
    """Marquer une commande comme prête"""
    order = get_object_or_404(Order, pk=pk)

    order.mark_ready()
    messages.success(request, f'Commande {order.order_number} marquée comme prête.')
    return redirect('orders:order_detail', pk=order.pk)


@login_required
@user_passes_test(can_manage_orders)
def order_mark_served(request, pk):
    """Marquer une commande comme servie"""
    order = get_object_or_404(Order, pk=pk)

    order.mark_served(request.user)
    messages.success(request, f'Commande {order.order_number} marquée comme servie.')
    return redirect('orders:order_detail', pk=order.pk)


@login_required
@user_passes_test(can_manage_orders)
def order_mark_paid(request, pk):
    """Marquer une commande comme payée"""
    order = get_object_or_404(Order, pk=pk)

    order.mark_paid()
    messages.success(request, f'Commande {order.order_number} marquée comme payée.')
    return redirect('orders:order_detail', pk=order.pk)


# ==================== CUISINE ====================
@login_required
@user_passes_test(can_manage_orders)
def kitchen_display(request):
    """Affichage cuisine (tickets en attente)"""
    tickets = KitchenTicket.objects.filter(
        status__in=['NEW', 'IN_PROGRESS']
    ).select_related('order').prefetch_related('order__items__menu_item').order_by('created_at')

    context = {
        'tickets': tickets,
    }

    return render(request, 'orders/kitchen_display.html', context)


@login_required
@user_passes_test(can_manage_orders)
def kitchen_ticket_start(request, pk):
    """Commencer un ticket de cuisine"""
    ticket = get_object_or_404(KitchenTicket, pk=pk)

    ticket.mark_in_progress()
    messages.success(request, f'Ticket {ticket.ticket_number} commencé.')
    return redirect('orders:kitchen_display')


@login_required
@user_passes_test(can_manage_orders)
def kitchen_ticket_complete(request, pk):
    """Terminer un ticket de cuisine"""
    ticket = get_object_or_404(KitchenTicket, pk=pk)

    ticket.mark_completed()
    messages.success(request, f'Ticket {ticket.ticket_number} terminé.')
    return redirect('orders:kitchen_display')


# ==================== RAPPORTS ====================
@login_required
@user_passes_test(can_manage_orders)
def orders_reports(request):
    """Page de rapports des commandes"""

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Statistiques globales
    total_orders = Order.objects.filter(
        order_date__date__gte=thirty_days_ago
    ).count()

    total_revenue = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='PAID'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    avg_order_value = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='PAID'
    ).aggregate(avg=Avg('total_amount'))['avg'] or 0

    # Plats les plus vendus
    top_selling_items = OrderItem.objects.filter(
        order__order_date__date__gte=thirty_days_ago,
        order__status='PAID'
    ).values('menu_item__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price'))
    ).order_by('-total_quantity')[:10]

    # Revenus par type de commande
    revenue_by_type = Order.objects.filter(
        order_date__date__gte=thirty_days_ago,
        status='PAID'
    ).values('order_type').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    )

    # Commandes par statut
    orders_by_status = Order.objects.filter(
        order_date__date__gte=thirty_days_ago
    ).values('status').annotate(count=Count('id'))

    context = {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'top_selling_items': top_selling_items,
        'revenue_by_type': revenue_by_type,
        'orders_by_status': orders_by_status,
    }

    return render(request, 'orders/reports.html', context)