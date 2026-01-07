from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from bookings.models import Table
from inventory.models import Product
from django.utils import timezone
from decimal import Decimal


class MenuCategory(models.Model):
    """Catégories du menu (Entrées, Plats, Desserts, Boissons, etc.)"""

    name = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icône FontAwesome')
    display_order = models.IntegerField(default=0, verbose_name='Ordre d\'affichage')
    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catégorie de menu'
        verbose_name_plural = 'Catégories de menu'
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name

    def get_menu_items_count(self):
        """Retourne le nombre de plats dans cette catégorie"""
        return self.menu_items.filter(is_available=True).count()


class MenuItem(models.Model):
    """Plats du menu"""

    name = models.CharField(max_length=200, verbose_name='Nom du plat')
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.PROTECT,
        related_name='menu_items',
        verbose_name='Catégorie'
    )

    description = models.TextField(blank=True, null=True, verbose_name='Description')
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Prix (€)'
    )

    # Gestion du stock
    track_inventory = models.BooleanField(
        default=False,
        verbose_name='Suivre le stock',
        help_text='Déduire automatiquement du stock quand commandé'
    )

    # Image du plat
    image = models.ImageField(
        upload_to='menu_items/',
        blank=True,
        null=True,
        verbose_name='Image'
    )

    # Informations nutritionnelles (optionnel)
    calories = models.IntegerField(blank=True, null=True, verbose_name='Calories')
    preparation_time = models.IntegerField(
        blank=True,
        null=True,
        verbose_name='Temps de préparation (min)'
    )

    is_available = models.BooleanField(default=True, verbose_name='Disponible')
    is_vegetarian = models.BooleanField(default=False, verbose_name='Végétarien')
    is_vegan = models.BooleanField(default=False, verbose_name='Végan')
    is_gluten_free = models.BooleanField(default=False, verbose_name='Sans gluten')
    is_spicy = models.BooleanField(default=False, verbose_name='Épicé')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plat'
        verbose_name_plural = 'Plats'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} - {self.price}€"


class MenuItemIngredient(models.Model):
    """Ingrédients nécessaires pour un plat (lien avec l'inventaire)"""

    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Plat'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='menu_items',
        verbose_name='Ingrédient'
    )
    quantity_needed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Quantité nécessaire'
    )

    class Meta:
        verbose_name = 'Ingrédient du plat'
        verbose_name_plural = 'Ingrédients des plats'
        unique_together = ['menu_item', 'product']

    def __str__(self):
        return f"{self.menu_item.name} - {self.product.name} ({self.quantity_needed})"


class Order(models.Model):
    """Commandes"""

    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmée'),
        ('PREPARING', 'En préparation'),
        ('READY', 'Prête'),
        ('SERVED', 'Servie'),
        ('PAID', 'Payée'),
        ('CANCELLED', 'Annulée'),
    ]

    ORDER_TYPE_CHOICES = [
        ('DINE_IN', 'Sur place'),
        ('TAKEAWAY', 'À emporter'),
        ('DELIVERY', 'Livraison'),
    ]

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='N° de commande'
    )

    # Informations de la commande
    order_type = models.CharField(
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='DINE_IN',
        verbose_name='Type de commande'
    )

    table = models.ForeignKey(
        Table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Table'
    )

    customer_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nom du client'
    )
    customer_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Téléphone'
    )

    # Statut et dates
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Statut'
    )

    order_date = models.DateTimeField(default=timezone.now, verbose_name='Date de commande')
    confirmed_at = models.DateTimeField(null=True, blank=True, verbose_name='Confirmée le')
    preparing_at = models.DateTimeField(null=True, blank=True, verbose_name='En préparation le')
    ready_at = models.DateTimeField(null=True, blank=True, verbose_name='Prête le')
    served_at = models.DateTimeField(null=True, blank=True, verbose_name='Servie le')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='Payée le')

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
        default=10,
        verbose_name='Taux de TVA (%)'
    )
    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant TVA (€)'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Remise (€)'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant total (€)'
    )

    # Notes
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders_created',
        verbose_name='Créé par'
    )
    served_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders_served',
        verbose_name='Servi par'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Commande'
        verbose_name_plural = 'Commandes'
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.order_number} - {self.get_status_display()}"

    def calculate_totals(self):
        """Calcule les totaux de la commande"""
        self.subtotal = sum(item.total_price() for item in self.items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        return self.total_amount

    def get_items_count(self):
        """Retourne le nombre d'articles dans la commande"""
        return self.items.count()

    def mark_confirmed(self):
        """Marque la commande comme confirmée"""
        self.status = 'CONFIRMED'
        self.confirmed_at = timezone.now()
        self.save()

    def mark_preparing(self):
        """Marque la commande comme en préparation"""
        self.status = 'PREPARING'
        self.preparing_at = timezone.now()
        self.save()

    def mark_ready(self):
        """Marque la commande comme prête"""
        self.status = 'READY'
        self.ready_at = timezone.now()
        self.save()

    def mark_served(self, user):
        """Marque la commande comme servie"""
        self.status = 'SERVED'
        self.served_at = timezone.now()
        self.served_by = user
        self.save()

    def mark_paid(self):
        """Marque la commande comme payée"""
        self.status = 'PAID'
        self.paid_at = timezone.now()
        self.save()

        # Créer une transaction de revenu
        from accounting.models import Transaction, AccountCategory
        revenue_category = AccountCategory.objects.filter(
            account_type='REVENUE'
        ).first()

        if revenue_category:
            Transaction.objects.create(
                transaction_number=f"TXN-{self.order_number}",
                transaction_type='INCOME',
                category=revenue_category,
                date=timezone.now().date(),
                amount=self.total_amount,
                payment_method='CASH',
                description=f"Commande {self.order_number}",
                created_by=self.served_by
            )


class OrderItem(models.Model):
    """Articles d'une commande"""

    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PREPARING', 'En préparation'),
        ('READY', 'Prêt'),
        ('SERVED', 'Servi'),
        ('CANCELLED', 'Annulé'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Commande'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name='Plat'
    )

    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Quantité'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Prix unitaire (€)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name='Statut'
    )

    special_instructions = models.TextField(
        blank=True,
        null=True,
        verbose_name='Instructions spéciales'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Article de commande'
        verbose_name_plural = 'Articles de commande'
        ordering = ['id']

    def __str__(self):
        return f"{self.menu_item.name} x{self.quantity}"

    def total_price(self):
        """Calcule le prix total de l'article"""
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        # Déduire du stock si nécessaire
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new and self.menu_item.track_inventory:
            self.deduct_from_inventory()

    def deduct_from_inventory(self):
        """Déduit les ingrédients du stock"""
        from inventory.models import StockMovement

        for ingredient in self.menu_item.ingredients.all():
            quantity_to_deduct = ingredient.quantity_needed * self.quantity

            # Créer un mouvement de stock
            StockMovement.objects.create(
                product=ingredient.product,
                movement_type='OUT',
                quantity=quantity_to_deduct,
                unit_price=ingredient.product.unit_price,
                reason=f'Commande {self.order.order_number} - {self.menu_item.name}',
                reference=self.order.order_number,
                created_by=self.order.created_by
            )


class KitchenTicket(models.Model):
    """Tickets de cuisine (pour la préparation)"""

    STATUS_CHOICES = [
        ('NEW', 'Nouveau'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminé'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='kitchen_tickets',
        verbose_name='Commande'
    )
    ticket_number = models.CharField(max_length=50, unique=True, verbose_name='N° ticket')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='NEW',
        verbose_name='Statut'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='Commencé à')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Terminé à')

    class Meta:
        verbose_name = 'Ticket de cuisine'
        verbose_name_plural = 'Tickets de cuisine'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.get_status_display()}"

    def mark_in_progress(self):
        """Marque le ticket comme en cours"""
        self.status = 'IN_PROGRESS'
        self.started_at = timezone.now()
        self.save()

        # Mettre à jour la commande
        self.order.mark_preparing()

    def mark_completed(self):
        """Marque le ticket comme terminé"""
        self.status = 'COMPLETED'
        self.completed_at = timezone.now()
        self.save()

        # Mettre à jour la commande
        self.order.mark_ready()