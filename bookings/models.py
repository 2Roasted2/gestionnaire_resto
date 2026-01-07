from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from django.utils import timezone
from datetime import datetime, timedelta


class TableLocation(models.Model):
    """Emplacements des tables (zones du restaurant)"""

    name = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Emplacement'
        verbose_name_plural = 'Emplacements'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_table_count(self):
        """Retourne le nombre de tables dans cet emplacement"""
        return self.tables.count()


class Table(models.Model):
    """Tables du restaurant"""

    table_number = models.CharField(max_length=20, unique=True, verbose_name='N° de table')
    location = models.ForeignKey(
        TableLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tables',
        verbose_name='Emplacement'
    )

    capacity = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        verbose_name='Capacité (personnes)'
    )

    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_available = models.BooleanField(default=True, verbose_name='Disponible')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Table'
        verbose_name_plural = 'Tables'
        ordering = ['table_number']

    def __str__(self):
        return f"Table {self.table_number} ({self.capacity} pers.)"

    def is_available_at(self, date, time_slot):
        """Vérifie si la table est disponible à une date et heure donnée"""
        # Vérifier s'il y a une réservation confirmée pour cette table à ce moment
        reservations = Reservation.objects.filter(
            table=self,
            reservation_date=date,
            time_slot=time_slot,
            status__in=['PENDING', 'CONFIRMED']
        )
        return not reservations.exists()


class Reservation(models.Model):
    """Réservations clients"""

    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmée'),
        ('CANCELLED', 'Annulée'),
        ('NO_SHOW', 'Client absent'),
        ('COMPLETED', 'Terminée'),
    ]

    TIME_SLOT_CHOICES = [
        ('11:30', '11:30'),
        ('12:00', '12:00'),
        ('12:30', '12:30'),
        ('13:00', '13:00'),
        ('13:30', '13:30'),
        ('14:00', '14:00'),
        ('19:00', '19:00'),
        ('19:30', '19:30'),
        ('20:00', '20:00'),
        ('20:30', '20:30'),
        ('21:00', '21:00'),
        ('21:30', '21:30'),
        ('22:00', '22:00'),
    ]

    reservation_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='N° de réservation'
    )

    # Informations client
    customer_name = models.CharField(max_length=200, verbose_name='Nom du client')
    customer_phone = models.CharField(max_length=20, verbose_name='Téléphone')
    customer_email = models.EmailField(blank=True, verbose_name='Email')

    # Détails de la réservation
    reservation_date = models.DateField(verbose_name='Date de réservation')
    time_slot = models.CharField(
        max_length=10,
        choices=TIME_SLOT_CHOICES,
        verbose_name='Créneau horaire'
    )
    number_of_guests = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(50)],
        verbose_name='Nombre de personnes'
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations',
        verbose_name='Table assignée'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Statut'
    )

    # Informations supplémentaires
    special_requests = models.TextField(
        blank=True,
        null=True,
        verbose_name='Demandes spéciales'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Notes internes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='reservations_created',
        verbose_name='Créé par'
    )
    confirmed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reservations_confirmed',
        verbose_name='Confirmé par'
    )
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmé le')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Réservation'
        verbose_name_plural = 'Réservations'
        ordering = ['-reservation_date', '-time_slot']
        unique_together = ['table', 'reservation_date', 'time_slot']

    def __str__(self):
        return f"{self.reservation_number} - {self.customer_name} - {self.reservation_date}"

    def is_past(self):
        """Vérifie si la réservation est passée"""
        reservation_datetime = datetime.combine(
            self.reservation_date,
            datetime.strptime(self.time_slot, '%H:%M').time()
        )
        return reservation_datetime < datetime.now()

    def is_today(self):
        """Vérifie si la réservation est pour aujourd'hui"""
        return self.reservation_date == timezone.now().date()

    def is_upcoming(self):
        """Vérifie si la réservation est à venir"""
        reservation_datetime = datetime.combine(
            self.reservation_date,
            datetime.strptime(self.time_slot, '%H:%M').time()
        )
        return reservation_datetime > datetime.now()

    def confirm(self, user):
        """Confirme la réservation"""
        self.status = 'CONFIRMED'
        self.confirmed_by = user
        self.confirmed_at = timezone.now()
        self.save()

    def cancel(self):
        """Annule la réservation"""
        self.status = 'CANCELLED'
        self.save()

    def complete(self):
        """Marque la réservation comme terminée"""
        self.status = 'COMPLETED'
        self.save()

    def mark_no_show(self):
        """Marque le client comme absent"""
        self.status = 'NO_SHOW'
        self.save()


class ReservationHistory(models.Model):
    """Historique des modifications de réservations"""

    ACTION_CHOICES = [
        ('CREATED', 'Créée'),
        ('CONFIRMED', 'Confirmée'),
        ('CANCELLED', 'Annulée'),
        ('MODIFIED', 'Modifiée'),
        ('COMPLETED', 'Terminée'),
        ('NO_SHOW', 'Client absent'),
    ]

    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='Réservation'
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        verbose_name='Action'
    )
    description = models.TextField(verbose_name='Description')

    # Traçabilité
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Effectué par'
    )
    performed_at = models.DateTimeField(auto_now_add=True, verbose_name='Effectué le')

    class Meta:
        verbose_name = 'Historique de réservation'
        verbose_name_plural = 'Historique des réservations'
        ordering = ['-performed_at']

    def __str__(self):
        return f"{self.reservation.reservation_number} - {self.get_action_display()} - {self.performed_at}"


class TimeSlotAvailability(models.Model):
    """Disponibilité des créneaux horaires par jour"""

    date = models.DateField(verbose_name='Date')
    time_slot = models.CharField(
        max_length=10,
        choices=Reservation.TIME_SLOT_CHOICES,
        verbose_name='Créneau horaire'
    )

    max_reservations = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        verbose_name='Réservations maximum'
    )
    is_available = models.BooleanField(default=True, verbose_name='Disponible')

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Disponibilité créneau'
        verbose_name_plural = 'Disponibilités créneaux'
        ordering = ['date', 'time_slot']
        unique_together = ['date', 'time_slot']

    def __str__(self):
        return f"{self.date} - {self.time_slot}"

    def get_current_reservations(self):
        """Retourne le nombre de réservations confirmées pour ce créneau"""
        return Reservation.objects.filter(
            reservation_date=self.date,
            time_slot=self.time_slot,
            status__in=['PENDING', 'CONFIRMED']
        ).count()

    def get_available_spots(self):
        """Retourne le nombre de places disponibles"""
        return self.max_reservations - self.get_current_reservations()

    def is_fully_booked(self):
        """Vérifie si le créneau est complet"""
        return self.get_available_spots() <= 0