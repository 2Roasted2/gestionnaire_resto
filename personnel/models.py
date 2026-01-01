from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import User
from django.utils import timezone
from decimal import Decimal


class Department(models.Model):
    """Départements du restaurant"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom du département')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name='Responsable'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_employee_count(self):
        """Retourne le nombre d'employés dans ce département"""
        return self.employees.filter(is_active=True).count()


class Employee(models.Model):
    """Profil détaillé des employés"""

    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('SINGLE', 'Célibataire'),
        ('MARRIED', 'Marié(e)'),
        ('DIVORCED', 'Divorcé(e)'),
        ('WIDOWED', 'Veuf/Veuve'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    employee_id = models.CharField(max_length=20, unique=True, verbose_name='Matricule')
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='employees',
        verbose_name='Département'
    )

    # Informations personnelles
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='Genre')
    marital_status = models.CharField(
        max_length=10,
        choices=MARITAL_STATUS_CHOICES,
        default='SINGLE',
        verbose_name='Situation matrimoniale'
    )
    nationality = models.CharField(max_length=50, default='Française', verbose_name='Nationalité')
    id_card_number = models.CharField(max_length=50, blank=True, verbose_name='N° Carte d\'identité')

    # Contact d'urgence
    emergency_contact_name = models.CharField(max_length=100, blank=True, verbose_name='Contact d\'urgence')
    emergency_contact_phone = models.CharField(max_length=20, blank=True, verbose_name='Tél. contact d\'urgence')
    emergency_contact_relation = models.CharField(max_length=50, blank=True, verbose_name='Lien de parenté')

    # Informations professionnelles
    hire_date = models.DateField(verbose_name='Date d\'embauche')
    end_date = models.DateField(null=True, blank=True, verbose_name='Date de fin')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    # Notes
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Employé'
        verbose_name_plural = 'Employés'
        ordering = ['-hire_date']

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"

    def get_years_of_service(self):
        """Calcule les années de service"""
        end = self.end_date if self.end_date else timezone.now().date()
        years = (end - self.hire_date).days / 365.25
        return round(years, 1)

    def get_current_contract(self):
        """Retourne le contrat actif"""
        return self.contracts.filter(
            is_active=True,
            start_date__lte=timezone.now().date()
        ).order_by('-start_date').first()


class Contract(models.Model):
    """Contrats de travail"""

    CONTRACT_TYPE_CHOICES = [
        ('CDI', 'CDI - Contrat à Durée Indéterminée'),
        ('CDD', 'CDD - Contrat à Durée Déterminée'),
        ('STAGE', 'Stage'),
        ('APPRENTISSAGE', 'Contrat d\'Apprentissage'),
        ('FREELANCE', 'Freelance/Prestation'),
        ('INTERIM', 'Intérim'),
    ]

    WORK_SCHEDULE_CHOICES = [
        ('FULL_TIME', 'Temps plein (35h/semaine)'),
        ('PART_TIME', 'Temps partiel'),
        ('VARIABLE', 'Horaires variables'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_TYPE_CHOICES, verbose_name='Type de contrat')

    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(null=True, blank=True, verbose_name='Date de fin')

    work_schedule = models.CharField(
        max_length=20,
        choices=WORK_SCHEDULE_CHOICES,
        default='FULL_TIME',
        verbose_name='Régime de travail'
    )
    weekly_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=35.00,
        verbose_name='Heures hebdomadaires'
    )

    # Rémunération
    base_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Salaire de base (€/mois)'
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Taux horaire (€/h)'
    )

    # Avantages
    meal_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Prime de repas (€/jour)'
    )
    transport_allowance = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Indemnité transport (€/mois)'
    )

    is_active = models.BooleanField(default=True, verbose_name='Contrat actif')

    document = models.FileField(
        upload_to='contracts/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Document du contrat'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Contrat'
        verbose_name_plural = 'Contrats'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.get_contract_type_display()}"

    def is_expired(self):
        """Vérifie si le contrat est expiré"""
        if self.end_date:
            return timezone.now().date() > self.end_date
        return False

    def calculate_monthly_gross(self):
        """Calcule le salaire brut mensuel avec primes"""
        gross = self.base_salary
        gross += self.transport_allowance
        # Approximation: 22 jours ouvrables par mois
        gross += (self.meal_allowance * Decimal('22'))
        return gross


class Attendance(models.Model):
    """Gestion des présences"""

    STATUS_CHOICES = [
        ('PRESENT', 'Présent'),
        ('ABSENT', 'Absent'),
        ('LATE', 'Retard'),
        ('LEAVE', 'Congé'),
        ('SICK', 'Maladie'),
        ('REMOTE', 'Télétravail'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(verbose_name='Date')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name='Statut')

    check_in = models.TimeField(null=True, blank=True, verbose_name='Heure d\'arrivée')
    check_out = models.TimeField(null=True, blank=True, verbose_name='Heure de départ')

    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Heures travaillées'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['-date']
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.date} - {self.get_status_display()}"

    def calculate_hours(self):
        """Calcule automatiquement les heures travaillées"""
        if self.check_in and self.check_out:
            from datetime import datetime, timedelta

            check_in_dt = datetime.combine(self.date, self.check_in)
            check_out_dt = datetime.combine(self.date, self.check_out)

            if check_out_dt < check_in_dt:
                check_out_dt += timedelta(days=1)

            delta = check_out_dt - check_in_dt
            self.hours_worked = Decimal(str(delta.total_seconds() / 3600))
            return self.hours_worked
        return None


class Leave(models.Model):
    """Gestion des congés"""

    LEAVE_TYPE_CHOICES = [
        ('ANNUAL', 'Congé annuel'),
        ('SICK', 'Congé maladie'),
        ('MATERNITY', 'Congé maternité'),
        ('PATERNITY', 'Congé paternité'),
        ('UNPAID', 'Congé sans solde'),
        ('FAMILY', 'Congé familial'),
        ('SPECIAL', 'Congé spécial'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('APPROVED', 'Approuvé'),
        ('REJECTED', 'Refusé'),
        ('CANCELLED', 'Annulé'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES, verbose_name='Type de congé')

    start_date = models.DateField(verbose_name='Date de début')
    end_date = models.DateField(verbose_name='Date de fin')

    days_count = models.IntegerField(verbose_name='Nombre de jours')
    reason = models.TextField(verbose_name='Motif')

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Statut'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        verbose_name='Approuvé par'
    )
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name='Date d\'approbation')

    rejection_reason = models.TextField(blank=True, null=True, verbose_name='Raison du refus')

    document = models.FileField(
        upload_to='leaves/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Justificatif'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Congé'
        verbose_name_plural = 'Congés'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.get_leave_type_display()} ({self.start_date})"

    def save(self, *args, **kwargs):
        """Calcule automatiquement le nombre de jours"""
        if self.start_date and self.end_date:
            delta = self.end_date - self.start_date
            self.days_count = delta.days + 1
        super().save(*args, **kwargs)


class Payroll(models.Model):
    """Fiches de paie"""

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payrolls')
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        verbose_name='Mois'
    )
    year = models.IntegerField(verbose_name='Année')

    # Salaire
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire de base')
    overtime_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        verbose_name='Heures supplémentaires'
    )
    overtime_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant heures sup.'
    )

    # Primes et avantages
    bonuses = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Primes')
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Indemnités')

    # Déductions
    absences_deduction = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Déduction absences'
    )
    social_security = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Cotisations sociales'
    )
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Impôts')
    other_deductions = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Autres déductions'
    )

    # Totaux
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire brut')
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Salaire net')

    # Statut
    is_paid = models.BooleanField(default=False, verbose_name='Payé')
    payment_date = models.DateField(null=True, blank=True, verbose_name='Date de paiement')
    payment_method = models.CharField(
        max_length=50,
        default='Virement bancaire',
        verbose_name='Mode de paiement'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fiche de paie'
        verbose_name_plural = 'Fiches de paie'
        ordering = ['-year', '-month']
        unique_together = ['employee', 'month', 'year']

    def __str__(self):
        return f"{self.employee.user.get_full_name()} - {self.month}/{self.year}"

    def calculate_totals(self):
        """Calcule les totaux automatiquement"""
        # Salaire brut
        self.gross_salary = (
                self.base_salary +
                self.overtime_amount +
                self.bonuses +
                self.allowances -
                self.absences_deduction
        )

        # Salaire net
        total_deductions = (
                self.social_security +
                self.tax +
                self.other_deductions
        )
        self.net_salary = self.gross_salary - total_deductions

        return self.net_salary