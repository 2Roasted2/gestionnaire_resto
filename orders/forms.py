from django import forms
from .models import MenuCategory, MenuItem, MenuItemIngredient, Order, OrderItem


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ['name', 'description', 'icon', 'display_order', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: fa-utensils'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = [
            'name', 'category', 'description', 'price', 'image',
            'track_inventory', 'calories', 'preparation_time',
            'is_available', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'track_inventory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control'}),
            'preparation_time': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_vegetarian': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_vegan': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_gluten_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_spicy': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MenuItemIngredientForm(forms.ModelForm):
    class Meta:
        model = MenuItemIngredient
        fields = ['product', 'quantity_needed']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity_needed': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'order_number', 'order_type', 'table', 'customer_name',
            'customer_phone', 'tax_rate', 'discount_amount', 'notes'
        ]
        widgets = {
            'order_number': forms.TextInput(attrs={'class': 'form-control'}),
            'order_type': forms.Select(attrs={'class': 'form-control'}),
            'table': forms.Select(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']
        widgets = {
            'menu_item': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'special_instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['menu_item'].queryset = MenuItem.objects.filter(is_available=True)


class QuickOrderForm(forms.Form):
    """Formulaire simplifié pour prise de commande rapide"""

    order_type = forms.ChoiceField(
        choices=Order.ORDER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Type de commande'
    )
    table = forms.ModelChoiceField(
        queryset=None,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Table',
        empty_label='Sélectionner une table'
    )
    customer_name = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du client'}),
        label='Nom du client'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from bookings.models import Table
        self.fields['table'].queryset = Table.objects.filter(is_available=True)


class OrderSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par n° commande, client...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Order.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    order_type = forms.ChoiceField(
        choices=[('', 'Tous les types')] + Order.ORDER_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )