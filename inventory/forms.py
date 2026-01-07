from django import forms
from .models import (
    Category, Supplier, Product, StockMovement,
    PurchaseOrder, PurchaseOrderItem, Inventory, InventoryItem
)


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: fa-carrot, fa-meat, fa-wine-bottle'
            }),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'name', 'contact_person', 'email', 'phone', 'address',
            'website', 'tax_id', 'payment_terms', 'is_active', 'notes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'payment_terms': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'reference', 'name', 'category', 'supplier', 'unit',
            'quantity_in_stock', 'minimum_stock', 'optimal_stock',
            'unit_price', 'description', 'barcode', 'image', 'is_active'
        ]
        widgets = {
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'quantity_in_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'optimal_stock': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        fields = ['product', 'movement_type', 'quantity', 'unit_price', 'reference', 'reason', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'movement_type': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.filter(is_active=True)


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'order_number', 'supplier', 'status', 'order_date',
            'expected_delivery_date', 'actual_delivery_date', 'notes'
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actual_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['product', 'quantity', 'unit_price', 'received_quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'received_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['inventory_number', 'inventory_date', 'status', 'notes']
        widgets = {
            'inventory_number': forms.TextInput(attrs={'class': 'form-control'}),
            'inventory_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['product', 'theoretical_quantity', 'physical_quantity', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'theoretical_quantity': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'physical_quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class ProductSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, référence...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Toutes les catégories'
    )
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label='Tous les fournisseurs'
    )
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('OUT_OF_STOCK', 'Rupture'),
            ('LOW_STOCK', 'Stock faible'),
            ('NORMAL', 'Normal'),
            ('OPTIMAL', 'Optimal'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )