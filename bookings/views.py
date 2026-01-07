from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta, date

from .models import (
    TableLocation, Table, Reservation,
    ReservationHistory, TimeSlotAvailability
)
from .forms import (
    TableLocationForm, TableForm, ReservationForm,
    QuickReservationForm, ReservationSearchForm,
    TimeSlotAvailabilityForm, AvailabilityCheckForm
)


# Décorateur pour vérifier les permissions
def can_manage_reservations(user):
    return user.is_authenticated and user.can_manage_reservations()


# ==================== DASHBOARD ====================
@login_required
@user_passes_test(can_manage_reservations)
def bookings_dashboard(request):
    """Tableau de bord du module Réservations"""

    today = timezone.now().date()

    # Réservations du jour
    today_reservations = Reservation.objects.filter(
        reservation_date=today
    ).count()

    # Réservations confirmées du jour
    confirmed_today = Reservation.objects.filter(
        reservation_date=today,
        status='CONFIRMED'
    ).count()

    # Réservations en attente
    pending_reservations = Reservation.objects.filter(
        status='PENDING'
    ).count()

    # Nombre total de tables
    total_tables = Table.objects.filter(is_available=True).count()

    # Prochaines réservations (aujourd'hui et demain)
    upcoming_reservations = Reservation.objects.filter(
        reservation_date__gte=today,
        reservation_date__lte=today + timedelta(days=1),
        status__in=['PENDING', 'CONFIRMED']
    ).select_related('table', 'created_by').order_by('reservation_date', 'time_slot')[:10]

    # Réservations récentes
    recent_reservations = Reservation.objects.select_related(
        'table', 'created_by'
    ).order_by('-created_at')[:5]

    # Statistiques par statut
    reservations_by_status = Reservation.objects.filter(
        reservation_date__gte=today - timedelta(days=30)
    ).values('status').annotate(count=Count('id'))

    # Créneaux les plus demandés
    popular_time_slots = Reservation.objects.filter(
        reservation_date__gte=today - timedelta(days=30),
        status__in=['CONFIRMED', 'COMPLETED']
    ).values('time_slot').annotate(count=Count('id')).order_by('-count')[:5]

    context = {
        'today_reservations': today_reservations,
        'confirmed_today': confirmed_today,
        'pending_reservations': pending_reservations,
        'total_tables': total_tables,
        'upcoming_reservations': upcoming_reservations,
        'recent_reservations': recent_reservations,
        'reservations_by_status': reservations_by_status,
        'popular_time_slots': popular_time_slots,
    }

    return render(request, 'bookings/dashboard.html', context)


# ==================== EMPLACEMENTS ====================
@login_required
@user_passes_test(can_manage_reservations)
def location_list(request):
    """Liste des emplacements"""
    locations = TableLocation.objects.all().annotate(
        table_count=Count('tables')
    )
    return render(request, 'bookings/location_list.html', {'locations': locations})


@login_required
@user_passes_test(can_manage_reservations)
def location_create(request):
    """Créer un emplacement"""
    if request.method == 'POST':
        form = TableLocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Emplacement créé avec succès.')
            return redirect('bookings:location_list')
    else:
        form = TableLocationForm()

    return render(request, 'bookings/location_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_reservations)
def location_update(request, pk):
    """Modifier un emplacement"""
    location = get_object_or_404(TableLocation, pk=pk)

    if request.method == 'POST':
        form = TableLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, 'Emplacement modifié avec succès.')
            return redirect('bookings:location_list')
    else:
        form = TableLocationForm(instance=location)

    return render(request, 'bookings/location_form.html', {
        'form': form,
        'location': location,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_reservations)
def location_delete(request, pk):
    """Supprimer un emplacement"""
    location = get_object_or_404(TableLocation, pk=pk)

    if request.method == 'POST':
        location.delete()
        messages.success(request, 'Emplacement supprimé avec succès.')
        return redirect('bookings:location_list')

    return render(request, 'bookings/location_confirm_delete.html', {'location': location})


# ==================== TABLES ====================
@login_required
@user_passes_test(can_manage_reservations)
def table_list(request):
    """Liste des tables"""
    tables = Table.objects.select_related('location').all()
    return render(request, 'bookings/table_list.html', {'tables': tables})


@login_required
@user_passes_test(can_manage_reservations)
def table_create(request):
    """Créer une table"""
    if request.method == 'POST':
        form = TableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table créée avec succès.')
            return redirect('bookings:table_list')
    else:
        form = TableForm()

    return render(request, 'bookings/table_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_reservations)
def table_update(request, pk):
    """Modifier une table"""
    table = get_object_or_404(Table, pk=pk)

    if request.method == 'POST':
        form = TableForm(request.POST, instance=table)
        if form.is_valid():
            form.save()
            messages.success(request, 'Table modifiée avec succès.')
            return redirect('bookings:table_list')
    else:
        form = TableForm(instance=table)

    return render(request, 'bookings/table_form.html', {
        'form': form,
        'table': table,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_reservations)
def table_delete(request, pk):
    """Supprimer une table"""
    table = get_object_or_404(Table, pk=pk)

    if request.method == 'POST':
        table.delete()
        messages.success(request, 'Table supprimée avec succès.')
        return redirect('bookings:table_list')

    return render(request, 'bookings/table_confirm_delete.html', {'table': table})


# ==================== RÉSERVATIONS ====================
@login_required
@user_passes_test(can_manage_reservations)
def reservation_list(request):
    """Liste des réservations avec recherche et filtres"""
    reservations = Reservation.objects.select_related('table', 'created_by').all()

    # Formulaire de recherche
    search_form = ReservationSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        status = search_form.cleaned_data.get('status')
        date_from = search_form.cleaned_data.get('date_from')
        date_to = search_form.cleaned_data.get('date_to')

        if search_query:
            reservations = reservations.filter(
                Q(reservation_number__icontains=search_query) |
                Q(customer_name__icontains=search_query) |
                Q(customer_phone__icontains=search_query) |
                Q(customer_email__icontains=search_query)
            )

        if status:
            reservations = reservations.filter(status=status)

        if date_from:
            reservations = reservations.filter(reservation_date__gte=date_from)

        if date_to:
            reservations = reservations.filter(reservation_date__lte=date_to)

    context = {
        'reservations': reservations,
        'search_form': search_form,
    }

    return render(request, 'bookings/reservation_list.html', context)


@login_required
@user_passes_test(can_manage_reservations)
def reservation_detail(request, pk):
    """Détails d'une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)
    history = reservation.history.select_related('performed_by').order_by('-performed_at')

    context = {
        'reservation': reservation,
        'history': history,
    }

    return render(request, 'bookings/reservation_detail.html', context)


@login_required
@user_passes_test(can_manage_reservations)
def reservation_create(request):
    """Créer une réservation"""
    if request.method == 'POST':
        form = ReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)

            # Générer un numéro de réservation si non fourni
            if not reservation.reservation_number:
                reservation.reservation_number = f"RES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            reservation.created_by = request.user
            reservation.save()

            # Créer une entrée dans l'historique
            ReservationHistory.objects.create(
                reservation=reservation,
                action='CREATED',
                description=f'Réservation créée pour {reservation.number_of_guests} personnes',
                performed_by=request.user
            )

            messages.success(request, 'Réservation créée avec succès.')
            return redirect('bookings:reservation_detail', pk=reservation.pk)
    else:
        # Générer un numéro de réservation automatique
        reservation_number = f"RES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        form = ReservationForm(initial={
            'reservation_number': reservation_number,
            'reservation_date': timezone.now().date(),
            'status': 'PENDING'
        })

    return render(request, 'bookings/reservation_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_reservations)
def reservation_quick_create(request):
    """Prise de réservation rapide"""
    if request.method == 'POST':
        form = QuickReservationForm(request.POST)
        if form.is_valid():
            reservation = form.save(commit=False)
            reservation.reservation_number = f"RES-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            reservation.created_by = request.user
            reservation.status = 'PENDING'
            reservation.save()

            # Créer une entrée dans l'historique
            ReservationHistory.objects.create(
                reservation=reservation,
                action='CREATED',
                description=f'Réservation rapide créée pour {reservation.number_of_guests} personnes',
                performed_by=request.user
            )

            messages.success(request, f'Réservation {reservation.reservation_number} créée avec succès.')
            return redirect('bookings:reservation_detail', pk=reservation.pk)
    else:
        form = QuickReservationForm(initial={
            'reservation_date': timezone.now().date()
        })

    return render(request, 'bookings/reservation_quick_form.html', {'form': form})


@login_required
@user_passes_test(can_manage_reservations)
def reservation_update(request, pk):
    """Modifier une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()

            # Créer une entrée dans l'historique
            ReservationHistory.objects.create(
                reservation=reservation,
                action='MODIFIED',
                description='Réservation modifiée',
                performed_by=request.user
            )

            messages.success(request, 'Réservation modifiée avec succès.')
            return redirect('bookings:reservation_detail', pk=reservation.pk)
    else:
        form = ReservationForm(instance=reservation)

    return render(request, 'bookings/reservation_form.html', {
        'form': form,
        'reservation': reservation,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_reservations)
def reservation_delete(request, pk):
    """Supprimer une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Réservation supprimée avec succès.')
        return redirect('bookings:reservation_list')

    return render(request, 'bookings/reservation_confirm_delete.html', {'reservation': reservation})


@login_required
@user_passes_test(can_manage_reservations)
def reservation_confirm(request, pk):
    """Confirmer une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.method == 'POST':
        reservation.confirm(request.user)

        # Créer une entrée dans l'historique
        ReservationHistory.objects.create(
            reservation=reservation,
            action='CONFIRMED',
            description='Réservation confirmée',
            performed_by=request.user
        )

        messages.success(request, 'Réservation confirmée avec succès.')
        return redirect('bookings:reservation_detail', pk=reservation.pk)

    return render(request, 'bookings/reservation_confirm.html', {'reservation': reservation})


@login_required
@user_passes_test(can_manage_reservations)
def reservation_cancel(request, pk):
    """Annuler une réservation"""
    reservation = get_object_or_404(Reservation, pk=pk)

    if request.method == 'POST':
        reservation.cancel()

        # Créer une entrée dans l'historique
        ReservationHistory.objects.create(
            reservation=reservation,
            action='CANCELLED',
            description='Réservation annulée',
            performed_by=request.user
        )

        messages.success(request, 'Réservation annulée.')
        return redirect('bookings:reservation_detail', pk=reservation.pk)

    return render(request, 'bookings/reservation_cancel.html', {'reservation': reservation})


@login_required
@user_passes_test(can_manage_reservations)
def reservation_complete(request, pk):
    """Marquer une réservation comme terminée"""
    reservation = get_object_or_404(Reservation, pk=pk)

    reservation.complete()

    # Créer une entrée dans l'historique
    ReservationHistory.objects.create(
        reservation=reservation,
        action='COMPLETED',
        description='Réservation terminée',
        performed_by=request.user
    )

    messages.success(request, 'Réservation marquée comme terminée.')
    return redirect('bookings:reservation_detail', pk=reservation.pk)


@login_required
@user_passes_test(can_manage_reservations)
def reservation_no_show(request, pk):
    """Marquer un client comme absent"""
    reservation = get_object_or_404(Reservation, pk=pk)

    reservation.mark_no_show()

    # Créer une entrée dans l'historique
    ReservationHistory.objects.create(
        reservation=reservation,
        action='NO_SHOW',
        description='Client absent (no-show)',
        performed_by=request.user
    )

    messages.warning(request, 'Client marqué comme absent.')
    return redirect('bookings:reservation_detail', pk=reservation.pk)


# ==================== PLANNING ====================
@login_required
@user_passes_test(can_manage_reservations)
def reservation_calendar(request):
    """Vue calendrier des réservations"""

    # Date sélectionnée (par défaut aujourd'hui)
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        selected_date = timezone.now().date()

    # Réservations du jour sélectionné
    reservations = Reservation.objects.filter(
        reservation_date=selected_date
    ).select_related('table').order_by('time_slot')

    # Statistiques du jour
    total_reservations = reservations.count()
    confirmed_count = reservations.filter(status='CONFIRMED').count()
    pending_count = reservations.filter(status='PENDING').count()
    total_guests = sum([r.number_of_guests for r in reservations])

    # Disponibilité par créneau
    time_slots_data = []
    for slot, slot_label in Reservation.TIME_SLOT_CHOICES:
        slot_reservations = reservations.filter(time_slot=slot)
        time_slots_data.append({
            'time': slot,
            'label': slot_label,
            'reservations': slot_reservations,
            'count': slot_reservations.count(),
            'guests': sum([r.number_of_guests for r in slot_reservations])
        })

    context = {
        'selected_date': selected_date,
        'reservations': reservations,
        'total_reservations': total_reservations,
        'confirmed_count': confirmed_count,
        'pending_count': pending_count,
        'total_guests': total_guests,
        'time_slots_data': time_slots_data,
    }

    return render(request, 'bookings/reservation_calendar.html', context)


# ==================== RAPPORTS ====================
@login_required
@user_passes_test(can_manage_reservations)
def bookings_reports(request):
    """Page de rapports et statistiques"""

    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Statistiques générales
    total_reservations = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago
    ).count()

    confirmed_reservations = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status='CONFIRMED'
    ).count()

    cancelled_reservations = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status='CANCELLED'
    ).count()

    no_show_count = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status='NO_SHOW'
    ).count()

    # Taux de confirmation
    confirmation_rate = (confirmed_reservations / total_reservations * 100) if total_reservations > 0 else 0

    # Réservations par statut
    reservations_by_status = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago
    ).values('status').annotate(count=Count('id'))

    # Créneaux horaires les plus populaires
    popular_time_slots = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status__in=['CONFIRMED', 'COMPLETED']
    ).values('time_slot').annotate(count=Count('id')).order_by('-count')

    # Nombre moyen de personnes par réservation
    avg_guests = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago
    ).aggregate(avg=Count('number_of_guests'))['avg'] or 0

    # Tables les plus réservées
    popular_tables = Reservation.objects.filter(
        reservation_date__gte=thirty_days_ago,
        status__in=['CONFIRMED', 'COMPLETED']
    ).values('table__table_number').annotate(count=Count('id')).order_by('-count')[:10]

    context = {
        'total_reservations': total_reservations,
        'confirmed_reservations': confirmed_reservations,
        'cancelled_reservations': cancelled_reservations,
        'no_show_count': no_show_count,
        'confirmation_rate': confirmation_rate,
        'reservations_by_status': reservations_by_status,
        'popular_time_slots': popular_time_slots,
        'avg_guests': avg_guests,
        'popular_tables': popular_tables,
    }

    return render(request, 'bookings/reports.html', context)