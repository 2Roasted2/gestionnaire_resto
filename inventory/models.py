from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import User
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    """Catégories de produits"""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nom')
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    icon = models.CharField(max_length=50, blank=True, verbose_name='Icône FontAwesome')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catégorie'
        verbose_name_plural = 'Catégories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_product_count(self):
        """Retourne le nombre de produits dans cette catégorie"""
        return self.products.count()


class Supplier(models.Model):
    """Fournisseurs"""
    name = models.CharField(max_length=200, unique=True, verbose_name='Nom')
    contact_person = models.CharField(max_length=100, blank=True, verbose_name='Personne de contact')
    email = models.EmailField(blank=True, verbose_name='Email')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    address = models.TextField(blank=True, verbose_name='Adresse')

    # Informations commerciales
    website = models.URLField(blank=True, verbose_name='Site web')
    tax_id = models.CharField(max_length=50, blank=True, verbose_name='N° SIRET/TVA')
    payment_terms = models.CharField(
        max_length=100,
        default='30 jours',
        verbose_name='Conditions de paiement'
    )

    is_active = models.BooleanField(default=True, verbose_name='Actif')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fournisseur'
        verbose_name_plural = 'Fournisseurs'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_product_count(self):
        """Retourne le nombre de produits fournis"""
        return self.products.count()


class Product(models.Model):
    """Produits et ingrédients en stock"""

    UNIT_CHOICES = [
        ('KG', 'Kilogramme'),
        ('G', 'Gramme'),
        ('L', 'Litre'),
        ('ML', 'Millilitre'),
        ('UNIT', 'Unité'),
        ('BOX', 'Boîte'),
        ('BOTTLE', 'Bouteille'),
        ('CAN', 'Canette'),
        ('PACKAGE', 'Paquet'),
    ]

    name = models.CharField(max_length=200, verbose_name='Nom')
    reference = models.CharField(max_length=50, unique=True, verbose_name='Référence')
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products',
        verbose_name='Catégorie'
    )
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Fournisseur principal'
    )

    # Unité et quantité
    unit = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default='UNIT',
        verbose_name='Unité de mesure'
    )
    quantity_in_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantité en stock'
    )
    minimum_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock minimum'
    )
    optimal_stock = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock optimal'
    )

    # Prix
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Prix unitaire (€)'
    )

    # Informations supplémentaires
    description = models.TextField(blank=True, null=True, verbose_name='Description')
    barcode = models.CharField(max_length=100, blank=True, verbose_name='Code-barres')
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        verbose_name='Image'
    )

    is_active = models.BooleanField(default=True, verbose_name='Actif')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Produit'
        verbose_name_plural = 'Produits'
        ordering = ['name']

    def __str__(self):
        return f"{self.reference} - {self.name}"

    def is_low_stock(self):
        """Vérifie si le stock est en dessous du minimum"""
        return self.quantity_in_stock < self.minimum_stock

    def stock_value(self):
        """Calcule la valeur totale du stock"""
        return self.quantity_in_stock * self.unit_price

    def stock_status(self):
        """Retourne le statut du stock"""
        if self.quantity_in_stock <= 0:
            return 'OUT_OF_STOCK'
        elif self.quantity_in_stock < self.minimum_stock:
            return 'LOW_STOCK'
        elif self.quantity_in_stock < self.optimal_stock:
            return 'NORMAL'
        else:
            return 'OPTIMAL'


class StockMovement(models.Model):
    """Mouvements de stock (entrées/sorties)"""

    MOVEMENT_TYPE_CHOICES = [
        ('IN', 'Entrée'),
        ('OUT', 'Sortie'),
        ('ADJUSTMENT', 'Ajustement'),
        ('RETURN', 'Retour'),
        ('WASTE', 'Perte/Gaspillage'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='movements',
        verbose_name='Produit'
    )
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES,
        verbose_name='Type de mouvement'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Quantité'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Prix unitaire (€)'
    )

    # Informations sur le mouvement
    reference = models.CharField(max_length=100, blank=True, verbose_name='Référence')
    reason = models.CharField(max_length=200, verbose_name='Motif')
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='stock_movements',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Date')

    class Meta:
        verbose_name = 'Mouvement de stock'
        verbose_name_plural = 'Mouvements de stock'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.name} - {self.quantity}"

    def total_value(self):
        """Calcule la valeur totale du mouvement"""
        return self.quantity * self.unit_price

    def save(self, *args, **kwargs):
        """Met à jour le stock du produit lors de la sauvegarde"""
        is_new = self.pk is None

        if is_new:
            # Nouveau mouvement
            if self.movement_type == 'IN':
                self.product.quantity_in_stock += self.quantity
            elif self.movement_type in ['OUT', 'WASTE']:
                self.product.quantity_in_stock -= self.quantity
            elif self.movement_type == 'ADJUSTMENT':
                # Pour les ajustements, la quantité peut être positive ou négative
                pass
            elif self.movement_type == 'RETURN':
                self.product.quantity_in_stock += self.quantity

            self.product.save()

        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """Bons de commande fournisseurs"""

    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SENT', 'Envoyé'),
        ('CONFIRMED', 'Confirmé'),
        ('RECEIVED', 'Reçu'),
        ('CANCELLED', 'Annulé'),
    ]

    order_number = models.CharField(max_length=50, unique=True, verbose_name='N° de commande')
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name='purchase_orders',
        verbose_name='Fournisseur'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        verbose_name='Statut'
    )

    order_date = models.DateField(verbose_name='Date de commande')
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de livraison prévue'
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Date de livraison réelle'
    )

    # Totaux
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Montant total (€)'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchase_orders',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Bon de commande'
        verbose_name_plural = 'Bons de commande'
        ordering = ['-order_date']

    def __str__(self):
        return f"{self.order_number} - {self.supplier.name}"

    def calculate_total(self):
        """Calcule le total de la commande"""
        total = sum(item.total_price() for item in self.items.all())
        self.total_amount = total
        return total

    def get_items_count(self):
        """Retourne le nombre d'articles dans la commande"""
        return self.items.count()


class PurchaseOrderItem(models.Model):
    """Lignes de commande"""

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Bon de commande'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='Produit'
    )

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

    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Quantité reçue'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    class Meta:
        verbose_name = 'Ligne de commande'
        verbose_name_plural = 'Lignes de commande'
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    def total_price(self):
        """Calcule le prix total de la ligne"""
        return self.quantity * self.unit_price

    def is_fully_received(self):
        """Vérifie si la quantité commandée a été entièrement reçue"""
        return self.received_quantity >= self.quantity


class Inventory(models.Model):
    """Inventaires physiques"""

    STATUS_CHOICES = [
        ('PLANNED', 'Planifié'),
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminé'),
        ('CANCELLED', 'Annulé'),
    ]

    inventory_number = models.CharField(max_length=50, unique=True, verbose_name='N° d\'inventaire')
    inventory_date = models.DateField(verbose_name='Date d\'inventaire')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PLANNED',
        verbose_name='Statut'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    # Traçabilité
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inventories',
        verbose_name='Créé par'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Inventaire'
        verbose_name_plural = 'Inventaires'
        ordering = ['-inventory_date']

    def __str__(self):
        return f"{self.inventory_number} - {self.inventory_date}"

    def get_items_count(self):
        """Retourne le nombre de produits inventoriés"""
        return self.items.count()

    def calculate_discrepancies(self):
        """Calcule les écarts entre stock théorique et stock physique"""
        discrepancies = []
        for item in self.items.all():
            diff = item.physical_quantity - item.theoretical_quantity
            if diff != 0:
                discrepancies.append({
                    'product': item.product,
                    'difference': diff,
                    'value': diff * item.product.unit_price
                })
        return discrepancies


class InventoryItem(models.Model):
    """Lignes d'inventaire"""

    inventory = models.ForeignKey(
        Inventory,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Inventaire'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='Produit'
    )

    theoretical_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Quantité théorique'
    )
    physical_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Quantité physique'
    )

    notes = models.TextField(blank=True, null=True, verbose_name='Notes')

    class Meta:
        verbose_name = 'Ligne d\'inventaire'
        verbose_name_plural = 'Lignes d\'inventaire'
        ordering = ['product__name']
        unique_together = ['inventory', 'product']

    def __str__(self):
        return f"{self.product.name} - {self.inventory.inventory_number}"

    def discrepancy(self):
        """Calcule l'écart entre stock théorique et physique"""
        return self.physical_quantity - self.theoretical_quantity

    def discrepancy_value(self):
        """Calcule la valeur de l'écart"""
        return self.discrepancy() * self.product.unit_price