from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from decimal import Decimal

from .models import (
    Category, Supplier, Product, StockMovement,
    PurchaseOrder, PurchaseOrderItem, Inventory, InventoryItem
)
from .forms import (
    CategoryForm, SupplierForm, ProductForm, StockMovementForm,
    PurchaseOrderForm, PurchaseOrderItemForm, InventoryForm,
    InventoryItemForm, ProductSearchForm
)


# Décorateur pour vérifier les permissions
def can_manage_inventory(user):
    return user.is_authenticated and user.can_manage_inventory()


# ==================== DASHBOARD ====================
@login_required
@user_passes_test(can_manage_inventory)
def inventory_dashboard(request):
    """Tableau de bord du module Inventory"""

    # Statistiques générales
    total_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.count()
    total_suppliers = Supplier.objects.filter(is_active=True).count()

    # Valeur totale du stock
    total_stock_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity_in_stock') * F('unit_price'))
    )['total'] or 0

    # Produits en rupture ou stock faible
    out_of_stock = Product.objects.filter(is_active=True, quantity_in_stock=0).count()
    low_stock = Product.objects.filter(
        is_active=True,
        quantity_in_stock__gt=0,
        quantity_in_stock__lt=F('minimum_stock')
    ).count()

    # Produits avec alerte
    alert_products = Product.objects.filter(
        is_active=True,
        quantity_in_stock__lt=F('minimum_stock')
    ).order_by('quantity_in_stock')[:5]

    # Derniers mouvements
    recent_movements = StockMovement.objects.select_related('product', 'created_by').order_by('-created_at')[:10]

    # Commandes en attente
    pending_orders = PurchaseOrder.objects.filter(
        status__in=['DRAFT', 'SENT', 'CONFIRMED']
    ).count()

    # Produits par catégorie
    products_by_category = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).values('name', 'product_count')

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_suppliers': total_suppliers,
        'total_stock_value': total_stock_value,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'alert_products': alert_products,
        'recent_movements': recent_movements,
        'pending_orders': pending_orders,
        'products_by_category': products_by_category,
    }

    return render(request, 'inventory/dashboard.html', context)


# ==================== CATÉGORIES ====================
@login_required
@user_passes_test(can_manage_inventory)
def category_list(request):
    """Liste des catégories"""
    categories = Category.objects.all().annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
@user_passes_test(can_manage_inventory)
def category_create(request):
    """Créer une catégorie"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie créée avec succès.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm()

    return render(request, 'inventory/category_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def category_update(request, pk):
    """Modifier une catégorie"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie modifiée avec succès.')
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=category)

    return render(request, 'inventory/category_form.html', {
        'form': form,
        'category': category,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_inventory)
def category_delete(request, pk):
    """Supprimer une catégorie"""
    category = get_object_or_404(Category, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Catégorie supprimée avec succès.')
        return redirect('inventory:category_list')

    return render(request, 'inventory/category_confirm_delete.html', {'category': category})


# ==================== FOURNISSEURS ====================
@login_required
@user_passes_test(can_manage_inventory)
def supplier_list(request):
    """Liste des fournisseurs"""
    suppliers = Supplier.objects.all().annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    )
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})


@login_required
@user_passes_test(can_manage_inventory)
def supplier_create(request):
    """Créer un fournisseur"""
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur créé avec succès.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()

    return render(request, 'inventory/supplier_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def supplier_update(request, pk):
    """Modifier un fournisseur"""
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fournisseur modifié avec succès.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)

    return render(request, 'inventory/supplier_form.html', {
        'form': form,
        'supplier': supplier,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_inventory)
def supplier_delete(request, pk):
    """Supprimer un fournisseur"""
    supplier = get_object_or_404(Supplier, pk=pk)

    if request.method == 'POST':
        supplier.delete()
        messages.success(request, 'Fournisseur supprimé avec succès.')
        return redirect('inventory:supplier_list')

    return render(request, 'inventory/supplier_confirm_delete.html', {'supplier': supplier})


# ==================== PRODUITS ====================
@login_required
@user_passes_test(can_manage_inventory)
def product_list(request):
    """Liste des produits avec recherche et filtres"""
    products = Product.objects.select_related('category', 'supplier').all()

    # Formulaire de recherche
    search_form = ProductSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        category = search_form.cleaned_data.get('category')
        supplier = search_form.cleaned_data.get('supplier')
        stock_status = search_form.cleaned_data.get('stock_status')

        if search_query:
            products = products.filter(
                Q(reference__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(barcode__icontains=search_query)
            )

        if category:
            products = products.filter(category=category)

        if supplier:
            products = products.filter(supplier=supplier)

        if stock_status:
            if stock_status == 'OUT_OF_STOCK':
                products = products.filter(quantity_in_stock=0)
            elif stock_status == 'LOW_STOCK':
                products = products.filter(
                    quantity_in_stock__gt=0,
                    quantity_in_stock__lt=F('minimum_stock')
                )
            elif stock_status == 'NORMAL':
                products = products.filter(
                    quantity_in_stock__gte=F('minimum_stock'),
                    quantity_in_stock__lt=F('optimal_stock')
                )
            elif stock_status == 'OPTIMAL':
                products = products.filter(quantity_in_stock__gte=F('optimal_stock'))

    context = {
        'products': products,
        'search_form': search_form,
    }

    return render(request, 'inventory/product_list.html', context)


@login_required
@user_passes_test(can_manage_inventory)
def product_detail(request, pk):
    """Détails d'un produit"""
    product = get_object_or_404(Product, pk=pk)

    # Derniers mouvements du produit
    movements = product.movements.select_related('created_by').order_by('-created_at')[:20]

    # Statistiques
    movements_in = product.movements.filter(movement_type='IN').aggregate(
        total=Sum('quantity')
    )['total'] or 0

    movements_out = product.movements.filter(movement_type='OUT').aggregate(
        total=Sum('quantity')
    )['total'] or 0

    context = {
        'product': product,
        'movements': movements,
        'movements_in': movements_in,
        'movements_out': movements_out,
    }

    return render(request, 'inventory/product_detail.html', context)


@login_required
@user_passes_test(can_manage_inventory)
def product_create(request):
    """Créer un produit"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit créé avec succès.')
            return redirect('inventory:product_list')
    else:
        form = ProductForm()

    return render(request, 'inventory/product_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def product_update(request, pk):
    """Modifier un produit"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Produit modifié avec succès.')
            return redirect('inventory:product_detail', pk=product.pk)
    else:
        form = ProductForm(instance=product)

    return render(request, 'inventory/product_form.html', {
        'form': form,
        'product': product,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_inventory)
def product_delete(request, pk):
    """Supprimer un produit"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Produit supprimé avec succès.')
        return redirect('inventory:product_list')

    return render(request, 'inventory/product_confirm_delete.html', {'product': product})


# Ajoutez ces vues à la suite du fichier inventory/views.py

# ==================== MOUVEMENTS DE STOCK ====================
@login_required
@user_passes_test(can_manage_inventory)
def stock_movement_list(request):
    """Liste des mouvements de stock"""
    movements = StockMovement.objects.select_related('product', 'created_by').all().order_by('-created_at')

    # Filtres optionnels
    movement_type = request.GET.get('type')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    return render(request, 'inventory/stock_movement_list.html', {'movements': movements})


@login_required
@user_passes_test(can_manage_inventory)
def stock_movement_create(request):
    """Créer un mouvement de stock"""
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user
            movement.save()
            messages.success(request, 'Mouvement de stock enregistré avec succès.')
            return redirect('inventory:stock_movement_list')
    else:
        form = StockMovementForm()

    return render(request, 'inventory/stock_movement_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def stock_movement_delete(request, pk):
    """Supprimer un mouvement de stock"""
    movement = get_object_or_404(StockMovement, pk=pk)

    if request.method == 'POST':
        # Annuler l'effet du mouvement sur le stock
        product = movement.product
        if movement.movement_type == 'IN':
            product.quantity_in_stock -= movement.quantity
        elif movement.movement_type in ['OUT', 'WASTE']:
            product.quantity_in_stock += movement.quantity
        elif movement.movement_type == 'RETURN':
            product.quantity_in_stock -= movement.quantity
        product.save()

        movement.delete()
        messages.success(request, 'Mouvement de stock supprimé avec succès.')
        return redirect('inventory:stock_movement_list')

    return render(request, 'inventory/stock_movement_confirm_delete.html', {'movement': movement})


# ==================== BONS DE COMMANDE ====================
@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_list(request):
    """Liste des bons de commande"""
    orders = PurchaseOrder.objects.select_related('supplier', 'created_by').all().order_by('-order_date')

    # Filtres optionnels
    status = request.GET.get('status')
    if status:
        orders = orders.filter(status=status)

    return render(request, 'inventory/purchase_order_list.html', {'orders': orders})


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_detail(request, pk):
    """Détails d'un bon de commande"""
    order = get_object_or_404(PurchaseOrder, pk=pk)
    items = order.items.select_related('product').all()

    context = {
        'order': order,
        'items': items,
    }

    return render(request, 'inventory/purchase_order_detail.html', context)


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_create(request):
    """Créer un bon de commande"""
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            messages.success(request, 'Bon de commande créé avec succès. Ajoutez maintenant des articles.')
            return redirect('inventory:purchase_order_add_item', pk=order.pk)
    else:
        # Générer un numéro de commande automatique
        from datetime import datetime
        order_number = f"PO-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = PurchaseOrderForm(initial={
            'order_number': order_number,
            'order_date': timezone.now().date(),
            'status': 'DRAFT'
        })

    return render(request, 'inventory/purchase_order_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_update(request, pk):
    """Modifier un bon de commande"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Bon de commande modifié avec succès.')
            return redirect('inventory:purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderForm(instance=order)

    return render(request, 'inventory/purchase_order_form.html', {
        'form': form,
        'order': order,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_delete(request, pk):
    """Supprimer un bon de commande"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Bon de commande supprimé avec succès.')
        return redirect('inventory:purchase_order_list')

    return render(request, 'inventory/purchase_order_confirm_delete.html', {'order': order})


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_add_item(request, pk):
    """Ajouter un article à un bon de commande"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_order = order
            item.save()

            # Recalculer le total de la commande
            order.calculate_total()
            order.save()

            messages.success(request, 'Article ajouté avec succès.')
            return redirect('inventory:purchase_order_detail', pk=order.pk)
    else:
        form = PurchaseOrderItemForm()

    items = order.items.select_related('product').all()

    return render(request, 'inventory/purchase_order_add_item.html', {
        'form': form,
        'order': order,
        'items': items,
    })


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_item_delete(request, pk):
    """Supprimer un article d'un bon de commande"""
    item = get_object_or_404(PurchaseOrderItem, pk=pk)
    order = item.purchase_order

    if request.method == 'POST':
        item.delete()

        # Recalculer le total de la commande
        order.calculate_total()
        order.save()

        messages.success(request, 'Article supprimé avec succès.')
        return redirect('inventory:purchase_order_detail', pk=order.pk)

    return render(request, 'inventory/purchase_order_item_confirm_delete.html', {
        'item': item,
        'order': order
    })


@login_required
@user_passes_test(can_manage_inventory)
def purchase_order_receive(request, pk):
    """Réceptionner une commande"""
    order = get_object_or_404(PurchaseOrder, pk=pk)

    if request.method == 'POST':
        # Créer les mouvements de stock pour chaque article
        for item in order.items.all():
            if item.received_quantity < item.quantity:
                # Quantité à réceptionner
                qty_to_receive = item.quantity - item.received_quantity

                # Créer le mouvement de stock
                StockMovement.objects.create(
                    product=item.product,
                    movement_type='IN',
                    quantity=qty_to_receive,
                    unit_price=item.unit_price,
                    reference=order.order_number,
                    reason=f'Réception commande {order.order_number}',
                    created_by=request.user
                )

                # Mettre à jour la quantité reçue
                item.received_quantity = item.quantity
                item.save()

        # Mettre à jour le statut de la commande
        order.status = 'RECEIVED'
        order.actual_delivery_date = timezone.now().date()
        order.save()

        messages.success(request, 'Commande réceptionnée avec succès.')
        return redirect('inventory:purchase_order_detail', pk=order.pk)

    return render(request, 'inventory/purchase_order_receive.html', {'order': order})


# ==================== INVENTAIRES ====================
@login_required
@user_passes_test(can_manage_inventory)
def inventory_list(request):
    """Liste des inventaires"""
    inventories = Inventory.objects.select_related('created_by').all().order_by('-inventory_date')
    return render(request, 'inventory/inventory_list.html', {'inventories': inventories})


@login_required
@user_passes_test(can_manage_inventory)
def inventory_detail(request, pk):
    """Détails d'un inventaire"""
    inventory = get_object_or_404(Inventory, pk=pk)
    items = inventory.items.select_related('product').all()

    # Calculer les écarts
    discrepancies = inventory.calculate_discrepancies()

    context = {
        'inventory': inventory,
        'items': items,
        'discrepancies': discrepancies,
    }

    return render(request, 'inventory/inventory_detail.html', context)


@login_required
@user_passes_test(can_manage_inventory)
def inventory_create(request):
    """Créer un inventaire"""
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            inventory = form.save(commit=False)
            inventory.created_by = request.user
            inventory.save()

            # Créer automatiquement les lignes d'inventaire pour tous les produits actifs
            products = Product.objects.filter(is_active=True)
            for product in products:
                InventoryItem.objects.create(
                    inventory=inventory,
                    product=product,
                    theoretical_quantity=product.quantity_in_stock,
                    physical_quantity=0
                )

            messages.success(request, f'Inventaire créé avec succès. {products.count()} produits ajoutés.')
            return redirect('inventory:inventory_detail', pk=inventory.pk)
    else:
        # Générer un numéro d'inventaire automatique
        from datetime import datetime
        inventory_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = InventoryForm(initial={
            'inventory_number': inventory_number,
            'inventory_date': timezone.now().date(),
            'status': 'PLANNED'
        })

    return render(request, 'inventory/inventory_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_inventory)
def inventory_update(request, pk):
    """Modifier un inventaire"""
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=inventory)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventaire modifié avec succès.')
            return redirect('inventory:inventory_detail', pk=inventory.pk)
    else:
        form = InventoryForm(instance=inventory)

    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'inventory': inventory,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_inventory)
def inventory_delete(request, pk):
    """Supprimer un inventaire"""
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == 'POST':
        inventory.delete()
        messages.success(request, 'Inventaire supprimé avec succès.')
        return redirect('inventory:inventory_list')

    return render(request, 'inventory/inventory_confirm_delete.html', {'inventory': inventory})


@login_required
@user_passes_test(can_manage_inventory)
def inventory_update_item(request, pk, item_pk):
    """Mettre à jour une ligne d'inventaire"""
    inventory = get_object_or_404(Inventory, pk=pk)
    item = get_object_or_404(InventoryItem, pk=item_pk, inventory=inventory)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ligne d\'inventaire mise à jour.')
            return redirect('inventory:inventory_detail', pk=inventory.pk)
    else:
        form = InventoryItemForm(instance=item)

    return render(request, 'inventory/inventory_item_form.html', {
        'form': form,
        'inventory': inventory,
        'item': item,
    })


@login_required
@user_passes_test(can_manage_inventory)
def inventory_complete(request, pk):
    """Finaliser un inventaire"""
    inventory = get_object_or_404(Inventory, pk=pk)

    if request.method == 'POST':
        # Créer des ajustements de stock pour les écarts
        discrepancies = inventory.calculate_discrepancies()

        for disc in discrepancies:
            StockMovement.objects.create(
                product=disc['product'],
                movement_type='ADJUSTMENT',
                quantity=abs(disc['difference']),
                unit_price=disc['product'].unit_price,
                reference=inventory.inventory_number,
                reason=f'Ajustement inventaire {inventory.inventory_number}',
                created_by=request.user
            )

            # Mettre à jour le stock du produit
            disc['product'].quantity_in_stock = inventory.items.get(
                product=disc['product']
            ).physical_quantity
            disc['product'].save()

        # Mettre à jour le statut de l'inventaire
        inventory.status = 'COMPLETED'
        inventory.save()

        messages.success(request, f'Inventaire finalisé. {len(discrepancies)} ajustements effectués.')
        return redirect('inventory:inventory_detail', pk=inventory.pk)

    discrepancies = inventory.calculate_discrepancies()

    return render(request, 'inventory/inventory_complete.html', {
        'inventory': inventory,
        'discrepancies': discrepancies,
    })


# ==================== RAPPORTS ====================
@login_required
@user_passes_test(can_manage_inventory)
def inventory_reports(request):
    """Page de rapports et statistiques"""

    # Statistiques générales
    total_products = Product.objects.filter(is_active=True).count()
    total_stock_value = Product.objects.filter(is_active=True).aggregate(
        total=Sum(F('quantity_in_stock') * F('unit_price'))
    )['total'] or 0

    # Produits par statut de stock
    out_of_stock = Product.objects.filter(is_active=True, quantity_in_stock=0).count()
    low_stock = Product.objects.filter(
        is_active=True,
        quantity_in_stock__gt=0,
        quantity_in_stock__lt=F('minimum_stock')
    ).count()
    optimal_stock = Product.objects.filter(
        is_active=True,
        quantity_in_stock__gte=F('optimal_stock')
    ).count()

    # Produits par catégorie
    products_by_category = Category.objects.annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).values('name', 'product_count')

    # Valeur du stock par catégorie
    stock_value_by_category = Category.objects.annotate(
        total_value=Sum(
            F('products__quantity_in_stock') * F('products__unit_price'),
            filter=Q(products__is_active=True)
        )
    ).values('name', 'total_value')

    # Top 10 produits les plus chers en stock
    top_value_products = Product.objects.filter(is_active=True).annotate(
        stock_value=F('quantity_in_stock') * F('unit_price')
    ).order_by('-stock_value')[:10]

    # Mouvements du mois
    current_month = timezone.now().month
    current_year = timezone.now().year

    movements_in = StockMovement.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year,
        movement_type='IN'
    ).aggregate(total=Sum('quantity'))['total'] or 0

    movements_out = StockMovement.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year,
        movement_type='OUT'
    ).aggregate(total=Sum('quantity'))['total'] or 0

    context = {
        'total_products': total_products,
        'total_stock_value': total_stock_value,
        'out_of_stock': out_of_stock,
        'low_stock': low_stock,
        'optimal_stock': optimal_stock,
        'products_by_category': products_by_category,
        'stock_value_by_category': stock_value_by_category,
        'top_value_products': top_value_products,
        'movements_in': movements_in,
        'movements_out': movements_out,
    }

    return render(request, 'inventory/reports.html', context)