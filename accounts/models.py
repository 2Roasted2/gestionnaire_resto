from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modèle utilisateur personnalisé avec gestion des rôles
    """
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('MANAGER', 'Manager'),
        ('WAITER', 'Serveur'),
        ('CHEF', 'Chef Cuisinier'),
        ('COOK', 'Cuisinier'),
        ('ACCOUNTANT', 'Comptable'),
        ('RECEPTIONIST', 'Réceptionniste'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='WAITER',
        verbose_name='Rôle'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Téléphone'
    )
    address = models.TextField(
        blank=True,
        null=True,
        verbose_name='Adresse'
    )
    photo = models.ImageField(
        upload_to='users/photos/',
        blank=True,
        null=True,
        verbose_name='Photo de profil'
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name='Date de naissance'
    )
    hire_date = models.DateField(
        auto_now_add=True,
        verbose_name='Date d\'embauche'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Actif'
    )

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name else self.username

    def has_role(self, role):
        """Vérifie si l'utilisateur a un rôle spécifique"""
        return self.role == role

    def can_manage_personnel(self):
        """Vérifie si l'utilisateur peut gérer le personnel"""
        return self.role in ['ADMIN', 'MANAGER']

    def can_manage_inventory(self):
        """Vérifie si l'utilisateur peut gérer le stock"""
        return self.role in ['ADMIN', 'MANAGER', 'CHEF']

    def can_manage_accounting(self):
        """Vérifie si l'utilisateur peut gérer la comptabilité"""
        return self.role in ['ADMIN', 'ACCOUNTANT']

    def can_manage_reservations(self):
        """Vérifie si l'utilisateur peut gérer les réservations"""
        return self.role in ['ADMIN', 'MANAGER', 'RECEPTIONIST']

    def can_manage_orders(self):
        """Vérifie si l'utilisateur peut gérer les commandes"""
        return self.role in ['ADMIN', 'MANAGER', 'WAITER', 'CHEF', 'COOK']