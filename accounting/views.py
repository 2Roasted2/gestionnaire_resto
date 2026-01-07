from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    AccountCategory, Transaction, Invoice, InvoiceItem,
    Payment, Budget
)
from .forms import (
    AccountCategoryForm, TransactionForm, InvoiceForm,
    InvoiceItemForm, PaymentForm, BudgetForm,
    TransactionSearchForm, InvoiceSearchForm
)


# Décorateur pour vérifier les permissions
def can_manage_accounting(user):
    return user.is_authenticated and user.can_manage_accounting()


# ==================== DASHBOARD ====================
@login_required
@user_passes_test(can_manage_accounting)
def accounting_dashboard(request):
    """Tableau de bord du module Comptabilité"""

    # Période actuelle
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Revenus du mois
    monthly_income = Transaction.objects.filter(
        transaction_type='INCOME',
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Dépenses du mois
    monthly_expenses = Transaction.objects.filter(
        transaction_type='EXPENSE',
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Balance du mois
    monthly_balance = monthly_income - monthly_expenses

    # Factures impayées
    unpaid_invoices = Invoice.objects.filter(
        status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE']
    ).aggregate(total=Sum(F('total_amount') - F('paid_amount')))['total'] or 0

    # Factures en retard
    overdue_invoices_count = Invoice.objects.filter(
        due_date__lt=today,
        status__in=['SENT', 'PARTIALLY_PAID', 'OVERDUE']
    ).count()

    # Dernières transactions
    recent_transactions = Transaction.objects.select_related(
        'category', 'created_by'
    ).order_by('-date', '-created_at')[:10]

    # Factures récentes
    recent_invoices = Invoice.objects.select_related('created_by').order_by('-issue_date')[:5]

    # Revenus vs dépenses par mois (6 derniers mois)
    months_data = []
    for i in range(5, -1, -1):
        month_date = today - timedelta(days=30 * i)
        month = month_date.month
        year = month_date.year

        income = Transaction.objects.filter(
            transaction_type='INCOME',
            date__month=month,
            date__year=year
        ).aggregate(total=Sum('amount'))['total'] or 0

        expense = Transaction.objects.filter(
            transaction_type='EXPENSE',
            date__month=month,
            date__year=year
        ).aggregate(total=Sum('amount'))['total'] or 0

        months_data.append({
            'month': month_date.strftime('%B'),
            'income': income,
            'expense': expense,
        })

    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'unpaid_invoices': unpaid_invoices,
        'overdue_invoices_count': overdue_invoices_count,
        'recent_transactions': recent_transactions,
        'recent_invoices': recent_invoices,
        'months_data': months_data,
    }

    return render(request, 'accounting/dashboard.html', context)


# ==================== CATÉGORIES DE COMPTES ====================
@login_required
@user_passes_test(can_manage_accounting)
def account_category_list(request):
    """Liste des catégories de comptes"""
    categories = AccountCategory.objects.all()
    return render(request, 'accounting/account_category_list.html', {'categories': categories})


@login_required
@user_passes_test(can_manage_accounting)
def account_category_create(request):
    """Créer une catégorie de compte"""
    if request.method == 'POST':
        form = AccountCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie créée avec succès.')
            return redirect('accounting:account_category_list')
    else:
        form = AccountCategoryForm()

    return render(request, 'accounting/account_category_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_accounting)
def account_category_update(request, pk):
    """Modifier une catégorie de compte"""
    category = get_object_or_404(AccountCategory, pk=pk)

    if request.method == 'POST':
        form = AccountCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Catégorie modifiée avec succès.')
            return redirect('accounting:account_category_list')
    else:
        form = AccountCategoryForm(instance=category)

    return render(request, 'accounting/account_category_form.html', {
        'form': form,
        'category': category,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_accounting)
def account_category_delete(request, pk):
    """Supprimer une catégorie de compte"""
    category = get_object_or_404(AccountCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Catégorie supprimée avec succès.')
        return redirect('accounting:account_category_list')

    return render(request, 'accounting/account_category_confirm_delete.html', {'category': category})


# ==================== TRANSACTIONS ====================
@login_required
@user_passes_test(can_manage_accounting)
def transaction_list(request):
    """Liste des transactions avec recherche et filtres"""
    transactions = Transaction.objects.select_related('category', 'created_by').all()

    # Formulaire de recherche
    search_form = TransactionSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        transaction_type = search_form.cleaned_data.get('transaction_type')
        category = search_form.cleaned_data.get('category')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')

        if search_query:
            transactions = transactions.filter(
                Q(transaction_number__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(reference__icontains=search_query)
            )

        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)

        if category:
            transactions = transactions.filter(category=category)

        if date_from:
            transactions = transactions.filter(date__gte=date_from)

        if date_to:
            transactions = transactions.filter(date__lte=date_to)

    # Calcul des totaux
    totals = {
        'income': transactions.filter(transaction_type='INCOME').aggregate(
            total=Sum('amount')
        )['total'] or 0,
        'expense': transactions.filter(transaction_type='EXPENSE').aggregate(
            total=Sum('amount')
        )['total'] or 0,
    }
    totals['balance'] = totals['income'] - totals['expense']

    context = {
        'transactions': transactions,
        'search_form': search_form,
        'totals': totals,
    }

    return render(request, 'accounting/transaction_list.html', context)


@login_required
@user_passes_test(can_manage_accounting)
def transaction_create(request):
    """Créer une transaction"""
    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, 'Transaction enregistrée avec succès.')
            return redirect('accounting:transaction_list')
    else:
        # Générer un numéro de transaction automatique
        transaction_number = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = TransactionForm(initial={
            'transaction_number': transaction_number,
            'date': timezone.now().date()
        })

    return render(request, 'accounting/transaction_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_accounting)
def transaction_update(request, pk):
    """Modifier une transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, request.FILES, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction modifiée avec succès.')
            return redirect('accounting:transaction_list')
    else:
        form = TransactionForm(instance=transaction)

    return render(request, 'accounting/transaction_form.html', {
        'form': form,
        'transaction': transaction,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_accounting)
def transaction_delete(request, pk):
    """Supprimer une transaction"""
    transaction = get_object_or_404(Transaction, pk=pk)

    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction supprimée avec succès.')
        return redirect('accounting:transaction_list')

    return render(request, 'accounting/transaction_confirm_delete.html', {'transaction': transaction})


# ==================== FACTURES ====================
@login_required
@user_passes_test(can_manage_accounting)
def invoice_list(request):
    """Liste des factures avec recherche et filtres"""
    invoices = Invoice.objects.select_related('created_by').all()

    # Formulaire de recherche
    search_form = InvoiceSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')

        if search_query:
            invoices = invoices.filter(
                Q(invoice_number__icontains=search_query) |
                Q(customer_name__icontains=search_query) |
                Q(customer_email__icontains=search_query)
            )

        if status:
            invoices = invoices.filter(status=status)

    # Calcul des totaux
    totals = {
        'total_amount': invoices.aggregate(total=Sum('total_amount'))['total'] or 0,
        'paid_amount': invoices.aggregate(total=Sum('paid_amount'))['total'] or 0,
    }
    totals['remaining'] = totals['total_amount'] - totals['paid_amount']

    context = {
        'invoices': invoices,
        'search_form': search_form,
        'totals': totals,
    }

    return render(request, 'accounting/invoice_list.html', context)


@login_required
@user_passes_test(can_manage_accounting)
def invoice_detail(request, pk):
    """Détails d'une facture"""
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    payments = invoice.payments.all().order_by('-payment_date')

    context = {
        'invoice': invoice,
        'items': items,
        'payments': payments,
    }

    return render(request, 'accounting/invoice_detail.html', context)


@login_required
@user_passes_test(can_manage_accounting)
def invoice_create(request):
    """Créer une facture"""
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            messages.success(request, 'Facture créée avec succès. Ajoutez maintenant des articles.')
            return redirect('accounting:invoice_add_item', pk=invoice.pk)
    else:
        # Générer un numéro de facture automatique
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = InvoiceForm(initial={
            'invoice_number': invoice_number,
            'issue_date': timezone.now().date(),
            'due_date': timezone.now().date() + timedelta(days=30),
            'status': 'DRAFT'
        })

    return render(request, 'accounting/invoice_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_accounting)
def invoice_update(request, pk):
    """Modifier une facture"""
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Facture modifiée avec succès.')
            return redirect('accounting:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'accounting/invoice_form.html', {
        'form': form,
        'invoice': invoice,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_accounting)
def invoice_delete(request, pk):
    """Supprimer une facture"""
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        invoice.delete()
        messages.success(request, 'Facture supprimée avec succès.')
        return redirect('accounting:invoice_list')

    return render(request, 'accounting/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
@user_passes_test(can_manage_accounting)
def invoice_add_item(request, pk):
    """Ajouter un article à une facture"""
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = InvoiceItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.invoice = invoice
            item.save()

            # Recalculer les totaux de la facture
            invoice.calculate_totals()
            invoice.save()

            messages.success(request, 'Article ajouté avec succès.')
            return redirect('accounting:invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceItemForm()

    items = invoice.items.all()

    return render(request, 'accounting/invoice_add_item.html', {
        'form': form,
        'invoice': invoice,
        'items': items,
    })


@login_required
@user_passes_test(can_manage_accounting)
def invoice_item_delete(request, pk):
    """Supprimer un article d'une facture"""
    item = get_object_or_404(InvoiceItem, pk=pk)
    invoice = item.invoice

    if request.method == 'POST':
        item.delete()

        # Recalculer les totaux de la facture
        invoice.calculate_totals()
        invoice.save()

        messages.success(request, 'Article supprimé avec succès.')
        return redirect('accounting:invoice_detail', pk=invoice.pk)

    return render(request, 'accounting/invoice_item_confirm_delete.html', {
        'item': item,
        'invoice': invoice
    })


@login_required
@user_passes_test(can_manage_accounting)
def invoice_add_payment(request, pk):
    """Ajouter un paiement à une facture"""
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.created_by = request.user
            payment.save()

            messages.success(request, 'Paiement enregistré avec succès.')
            return redirect('accounting:invoice_detail', pk=invoice.pk)
    else:
        # Générer un numéro de paiement automatique
        payment_number = f"PAY-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = PaymentForm(initial={
            'payment_number': payment_number,
            'payment_date': timezone.now().date(),
            'amount': invoice.remaining_balance()
        })

    return render(request, 'accounting/payment_form.html', {
        'form': form,
        'invoice': invoice,
        'action': 'Ajouter'
    })


# ==================== RAPPORTS ====================
@login_required
@user_passes_test(can_manage_accounting)
def accounting_reports(request):
    """Page de rapports financiers"""

    # Période actuelle
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Revenus et dépenses par catégorie (mois actuel)
    income_by_category = Transaction.objects.filter(
        transaction_type='INCOME',
        date__month=current_month,
        date__year=current_year
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    expense_by_category = Transaction.objects.filter(
        transaction_type='EXPENSE',
        date__month=current_month,
        date__year=current_year
    ).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')

    # Totaux annuels
    yearly_income = Transaction.objects.filter(
        transaction_type='INCOME',
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    yearly_expense = Transaction.objects.filter(
        transaction_type='EXPENSE',
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or 0

    yearly_balance = yearly_income - yearly_expense

    # Factures par statut
    invoices_by_status = Invoice.objects.values('status').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )

    # Revenus par mode de paiement
    payment_methods = Transaction.objects.filter(
        transaction_type='INCOME',
        date__month=current_month,
        date__year=current_year
    ).values('payment_method').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'income_by_category': income_by_category,
        'expense_by_category': expense_by_category,
        'yearly_income': yearly_income,
        'yearly_expense': yearly_expense,
        'yearly_balance': yearly_balance,
        'invoices_by_status': invoices_by_status,
        'payment_methods': payment_methods,
    }

    return render(request, 'accounting/reports.html', context)