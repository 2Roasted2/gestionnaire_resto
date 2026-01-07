from django import forms
from .models import (
    AccountCategory, Transaction, Invoice, InvoiceItem,
    Payment, Budget
)


class AccountCategoryForm(forms.ModelForm):
    class Meta:
        model = AccountCategory
        fields = ['code', 'name', 'account_type', 'description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'transaction_number', 'transaction_type', 'category', 'date',
            'amount', 'payment_method', 'reference', 'description', 'notes', 'receipt'
        ]
        widgets = {
            'transaction_number': forms.TextInput(attrs={'class': 'form-control'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = AccountCategory.objects.filter(is_active=True)


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'customer_name', 'customer_email', 'customer_phone',
            'customer_address', 'issue_date', 'due_date', 'tax_rate', 'status', 'notes'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['payment_number', 'payment_date', 'amount', 'payment_method', 'reference', 'notes']
        widgets = {
            'payment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['category', 'period', 'year', 'month', 'budgeted_amount', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
            'year': forms.NumberInput(attrs={'class': 'form-control', 'min': '2020', 'max': '2030'}),
            'month': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '12'}),
            'budgeted_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class TransactionSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro, description...'
        })
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Transaction.TRANSACTION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    category = forms.ModelChoiceField(
        queryset=AccountCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Toutes les catégories'
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )


class InvoiceSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par numéro, client...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Invoice.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )