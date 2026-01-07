from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from decimal import Decimal
from django.utils import timezone


class AccountCategory(models.Model):
    """Catégories de comptes comptables"""

    ACCOUNT_TYPE_CHOICES = [
        ('ASSET', 'Actif'),
        ('LIABILITY', 'Passif'),
        ('EQUITY', 'Capitaux propres'),
        ('REVENUE', 'Revenus'),
        ('EXPENSE', 'Dépenses'),
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name='Nom')
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPE_CHOICES,
        verbose_name='Type de compte'
    )
    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catégorie de compte'
        verbose_name_plural = 'Catégories de comptes'
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Transaction(models.Model):
    """Transactions financières (revenus et dépenses)"""

    TRANSACTION_TYPE_CHOICES = [
        ('INCOME', 'Revenu'),
        ('EXPENSE', 'Dépense'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Espèces'),
        ('CARD', 'Carte bancaire'),
        ('BANK_TRANSFER', 'Virement bancaire'),
        ('CHECK', 'Chèque'),
        ('MOBILE_PAYMENT', 'Paiement mobile'),
        ('OTHER', 'Autre'),
    ]

    transaction_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='N° de transaction'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        verbose_name='Type'
    )
    category = models.ForeignKey(
        AccountCategory,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name='Catégorie'
    )

    date = models.DateField(verbose_name='Date')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant (€)'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Mode de paiement'
    )

    reference = models.CharField(max_length=100, blank=True, verbose_name='Référence')
    description = models.TextField(verbose_name='Description')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Documents
    receipt = models.FileField(
        upload_to='accounting/receipts/',
        blank=True,
        null=True,
        verbose_name='Reçu/Facture'
    )

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='transactions',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - {self.amount}€"


class Invoice(models.Model):
    """Factures clients"""

    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SENT', 'Envoyée'),
        ('PAID', 'Payée'),
        ('PARTIALLY_PAID', 'Partiellement payée'),
        ('OVERDUE', 'En retard'),
        ('CANCELLED', 'Annulée'),
    ]

    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='N° de facture'
    )
    customer_name = models.CharField(max_length=200, verbose_name='Nom du client')
    customer_email = models.EmailField(blank=True, verbose_name='Email du client')
    customer_phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    customer_address = models.TextField(blank=True, verbose_name='Adresse')

    issue_date = models.DateField(verbose_name='Date d\'émission')
    due_date = models.DateField(verbose_name='Date d\'échéance')

    # Montants
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Sous-total (€)'
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=20,
        verbose_name='Taux de TVA (%)'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant TVA (€)'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant total (€)'
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant payé (€)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='Statut'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invoices',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-issue_date']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer_name}"

    def calculate_totals(self):
        """Calcule les totaux de la facture"""
        self.subtotal = sum(item.total_price() for item in self.items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount
        return self.total_amount

    def remaining_balance(self):
        """Calcule le solde restant"""
        return self.total_amount - self.paid_amount

    def is_overdue(self):
        """Vérifie si la facture est en retard"""
        return self.due_date < timezone.now().date() and self.status not in ['PAID', 'CANCELLED']

    def update_status(self):
        """Met à jour le statut en fonction des paiements"""
        if self.paid_amount >= self.total_amount:
            self.status = 'PAID'
        elif self.paid_amount > 0:
            self.status = 'PARTIALLY_PAID'
        elif self.is_overdue():
            self.status = 'OVERDUE'


class InvoiceItem(models.Model):
    """Lignes de facture"""

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Facture'
    )
    description = models.CharField(max_length=200, verbose_name='Description')
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Quantité'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Prix unitaire (€)'
    )

    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'
        ordering = ['id']

    def __str__(self):
        return f"{self.description} - {self.quantity} x {self.unit_price}€"

    def total_price(self):
        """Calcule le prix total de la ligne"""
        return self.quantity * self.unit_price


class Payment(models.Model):
    """Paiements reçus"""

    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Espèces'),
        ('CARD', 'Carte bancaire'),
        ('BANK_TRANSFER', 'Virement bancaire'),
        ('CHECK', 'Chèque'),
        ('MOBILE_PAYMENT', 'Paiement mobile'),
        ('OTHER', 'Autre'),
    ]

    payment_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='N° de paiement'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Facture'
    )

    payment_date = models.DateField(verbose_name='Date de paiement')
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant (€)'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name='Mode de paiement'
    )

    reference = models.CharField(max_length=100, blank=True, verbose_name='Référence')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payments',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.payment_number} - {self.amount}€"

    def save(self, *args, **kwargs):
        """Met à jour le montant payé de la facture"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Mettre à jour le montant payé de la facture
            self.invoice.paid_amount += self.amount
            self.invoice.update_status()
            self.invoice.save()


class Budget(models.Model):
    """Budgets par catégorie"""

    PERIOD_CHOICES = [
        ('MONTHLY', 'Mensuel'),
        ('QUARTERLY', 'Trimestriel'),
        ('YEARLY', 'Annuel'),
    ]

    category = models.ForeignKey(
        AccountCategory,
        on_delete=models.CASCADE,
        related_name='budgets',
        verbose_name='Catégorie'
    )

    period = models.CharField(
        max_length=20,
        choices=PERIOD_CHOICES,
        verbose_name='Période'
    )
    year = models.IntegerField(verbose_name='Année')
    month = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Mois',
        help_text='Requis pour les budgets mensuels'
    )

    budgeted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Montant budgété (€)'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        ordering = ['-year', '-month']
        unique_together = ['category', 'period', 'year', 'month']

    def __str__(self):
        if self.period == 'MONTHLY':
            return f"{self.category.name} - {self.month}/{self.year}"
        return f"{self.category.name} - {self.year}"

    def get_actual_amount(self):
        """Calcule le montant réel dépensé/gagné"""
        from django.db.models import Sum

        # Filtrer les transactions selon la période
        transactions = Transaction.objects.filter(category=self.category)

        if self.period == 'MONTHLY':
            transactions = transactions.filter(
                date__year=self.year,
                date__month=self.month
            )
        elif self.period == 'QUARTERLY':
            quarter_start = ((self.month - 1) // 3) * 3 + 1
            quarter_end = quarter_start + 2
            transactions = transactions.filter(
                date__year=self.year,
                date__month__gte=quarter_start,
                date__month__lte=quarter_end
            )
        else:  # YEARLY
            transactions = transactions.filter(date__year=self.year)

        total = transactions.aggregate(total=Sum('amount'))['total'] or 0
        return total

    def get_variance(self):
        """Calcule l'écart entre budget et réel"""
        actual = self.get_actual_amount()
        return self.budgeted_amount - actual

    def get_percentage_used(self):
        """Calcule le pourcentage utilisé"""
        if self.budgeted_amount == 0:
            return 0
        actual = self.get_actual_amount()
        return (actual / self.budgeted_amount) * 100