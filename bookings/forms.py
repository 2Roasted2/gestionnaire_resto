from django import forms
from .models import TableLocation, Table, Reservation, TimeSlotAvailability
from datetime import date


class TableLocationForm(forms.ModelForm):
    class Meta:
        model = TableLocation
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['table_number', 'location', 'capacity', 'description', 'is_available']
        widgets = {
            'table_number': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '20'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'reservation_number', 'customer_name', 'customer_phone', 'customer_email',
            'reservation_date', 'time_slot', 'number_of_guests', 'table',
            'status', 'special_requests', 'notes'
        ]
        widgets = {
            'reservation_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'reservation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'number_of_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50'}),
            'table': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'special_requests': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['table'].queryset = Table.objects.filter(is_available=True)
        self.fields['table'].required = False


class QuickReservationForm(forms.ModelForm):
    """Formulaire simplifié pour prise de réservation rapide"""

    class Meta:
        model = Reservation
        fields = [
            'customer_name', 'customer_phone', 'customer_email',
            'reservation_date', 'time_slot', 'number_of_guests',
            'special_requests'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom complet'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '06 12 34 56 78'}),
            'customer_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'email@exemple.com'}),
            'reservation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'number_of_guests': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50'}),
            'special_requests': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Allergies, occasion spéciale...'}),
        }


class ReservationSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher par nom, téléphone, n° réservation...'
        })
    )
    status = forms.ChoiceField(
        choices=[('', 'Tous les statuts')] + Reservation.STATUS_CHOICES,
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


class TimeSlotAvailabilityForm(forms.ModelForm):
    class Meta:
        model = TimeSlotAvailability
        fields = ['date', 'time_slot', 'max_reservations', 'is_available', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'max_reservations': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class AvailabilityCheckForm(forms.Form):
    """Formulaire de vérification de disponibilité"""

    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='Date'
    )
    time_slot = forms.ChoiceField(
        choices=Reservation.TIME_SLOT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Créneau horaire'
    )
    number_of_guests = forms.IntegerField(
        min_value=1,
        max_value=50,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '50'}),
        label='Nombre de personnes'
    )