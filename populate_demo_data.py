"""
Script de génération de données de démonstration pour Restaurant Manager
Exécuter avec: python populate_demo_data.py
"""

import os
import django
import random
from datetime import datetime, timedelta, date
from decimal import Decimal

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Resto_gestion.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import User
from personnel.models import Department, Employee, Contract, Attendance, Leave, Payroll
from inventory.models import Category as InventoryCategory, Supplier, Product, StockMovement
from accounting.models import AccountCategory, Transaction, Invoice, Payment
from bookings.models import TableLocation, Table, Reservation
from orders.models import MenuCategory, MenuItem, MenuItemIngredient, Order, OrderItem, KitchenTicket

print("🚀 Début de la génération des données de démonstration...")

# ==================== NETTOYAGE ====================
def clean_database():
    """Nettoie toutes les données existantes (ATTENTION : supprime tout !)"""
    response = input("⚠️  Voulez-vous supprimer toutes les données existantes ? (oui/non): ")
    if response.lower() == 'oui':
        print("🗑️  Nettoyage de la base de données...")

        # Ordre important pour respecter les contraintes de clés étrangères
        KitchenTicket.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        MenuItemIngredient.objects.all().delete()
        MenuItem.objects.all().delete()
        MenuCategory.objects.all().delete()

        Reservation.objects.all().delete()
        Table.objects.all().delete()
        TableLocation.objects.all().delete()

        Payment.objects.all().delete()
        Invoice.objects.all().delete()
        Transaction.objects.all().delete()
        AccountCategory.objects.all().delete()

        StockMovement.objects.all().delete()
        Product.objects.all().delete()
        Supplier.objects.all().delete()
        InventoryCategory.objects.all().delete()

        Payroll.objects.all().delete()
        Leave.objects.all().delete()
        Attendance.objects.all().delete()
        Contract.objects.all().delete()
        Employee.objects.all().delete()
        Department.objects.all().delete()

        User.objects.filter(is_superuser=False).delete()

        print("✅ Base de données nettoyée !")

# Appel de la fonction de nettoyage
clean_database()

# ==================== 1. UTILISATEURS & COMPTES ====================
print("\n👥 Création des utilisateurs...")

users_data = [
    {
        'username': 'admin',
        'email': 'admin@restaurant.com',
        'password': 'admin123',
        'first_name': 'Admin',
        'last_name': 'Système',
        'role': 'ADMIN',
        'is_superuser': True,
        'is_staff': True
    },
    {
        'username': 'manager',
        'email': 'manager@restaurant.com',
        'password': 'manager123',
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'role': 'MANAGER'
    },
    {
        'username': 'chef',
        'email': 'chef@restaurant.com',
        'password': 'chef123',
        'first_name': 'Pierre',
        'last_name': 'Martin',
        'role': 'CHEF'
    },
    {
        'username': 'serveur1',
        'email': 'serveur1@restaurant.com',
        'password': 'serveur123',
        'first_name': 'Marie',
        'last_name': 'Dubois',
        'role': 'WAITER'
    },
    {
        'username': 'serveur2',
        'email': 'serveur2@restaurant.com',
        'password': 'serveur123',
        'first_name': 'Sophie',
        'last_name': 'Bernard',
        'role': 'WAITER'
    },
    {
        'username': 'cuisinier',
        'email': 'cuisinier@restaurant.com',
        'password': 'cuisinier123',
        'first_name': 'Thomas',
        'last_name': 'Petit',
        'role': 'COOK'
    },
]

users = {}
for user_data in users_data:
    username = user_data['username']
    if not User.objects.filter(username=username).exists():
        password = user_data.pop('password')
        is_superuser = user_data.pop('is_superuser', False)
        is_staff = user_data.pop('is_staff', False)

        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.save()
        users[username] = user
        print(f"  ✅ Utilisateur créé: {username} (mot de passe: {password})")
    else:
        users[username] = User.objects.get(username=username)
        print(f"  ⏭️  Utilisateur existant: {username}")

# ==================== 2. DÉPARTEMENTS & EMPLOYÉS ====================
print("\n🏢 Création des départements...")

departments_data = [
    {'name': 'Direction', 'description': 'Direction et management'},
    {'name': 'Cuisine', 'description': 'Brigade de cuisine'},
    {'name': 'Salle', 'description': 'Service en salle'},
    {'name': 'Bar', 'description': 'Service bar et boissons'},
]

departments = {}
for dept_data in departments_data:
    dept, created = Department.objects.get_or_create(
        name=dept_data['name'],
        defaults={'description': dept_data['description']}
    )
    departments[dept_data['name']] = dept
    print(f"  {'✅' if created else '⏭️ '} Département: {dept.name}")

print("\n👨‍💼 Création des profils employés...")

employees_data = [
    {
        'user': users['manager'],
        'employee_id': 'EMP001',
        'department': departments['Direction'],
        'gender': 'M',
        'nationality': 'Française',
        'hire_date': date.today() - timedelta(days=1825),  # 5 ans
    },
    {
        'user': users['chef'],
        'employee_id': 'EMP002',
        'department': departments['Cuisine'],
        'gender': 'M',
        'nationality': 'Française',
        'hire_date': date.today() - timedelta(days=1095),  # 3 ans
    },
    {
        'user': users['serveur1'],
        'employee_id': 'EMP003',
        'department': departments['Salle'],
        'gender': 'F',
        'nationality': 'Française',
        'hire_date': date.today() - timedelta(days=730),  # 2 ans
    },
    {
        'user': users['serveur2'],
        'employee_id': 'EMP004',
        'department': departments['Salle'],
        'gender': 'F',
        'nationality': 'Française',
        'hire_date': date.today() - timedelta(days=365),  # 1 an
    },
    {
        'user': users['cuisinier'],
        'employee_id': 'EMP005',
        'department': departments['Cuisine'],
        'gender': 'M',
        'nationality': 'Française',
        'hire_date': date.today() - timedelta(days=545),  # 1.5 ans
    },
]

employees = {}
for emp_data in employees_data:
    emp, created = Employee.objects.get_or_create(
        user=emp_data['user'],
        defaults=emp_data
    )
    employees[emp_data['user'].username] = emp
    print(f"  {'✅' if created else '⏭️ '} Employé: {emp.user.get_full_name()} ({emp.employee_id})")

# Contrats
print("\n📄 Création des contrats...")
for username, emp in employees.items():
    if not Contract.objects.filter(employee=emp).exists():
        Contract.objects.create(
            employee=emp,
            contract_type='CDI',
            start_date=emp.hire_date,
            work_schedule='FULL_TIME',
            weekly_hours=Decimal('35.00'),
            base_salary=Decimal(random.choice(['2000', '2500', '3000', '3500'])),
            is_active=True
        )
        print(f"  ✅ Contrat créé pour {emp.user.get_full_name()}")

# Présences (dernier mois)
print("\n📅 Création des présences...")
today = date.today()
for i in range(20):  # 20 derniers jours
    attendance_date = today - timedelta(days=i)
    if attendance_date.weekday() < 5:  # Lundi à Vendredi
        for emp in employees.values():
            if not Attendance.objects.filter(employee=emp, date=attendance_date).exists():
                Attendance.objects.create(
                    employee=emp,
                    date=attendance_date,
                    status='PRESENT',
                    check_in='09:00:00',
                    check_out='18:00:00',
                    hours_worked=Decimal('8.00')
                )
print(f"  ✅ {Attendance.objects.count()} présences créées")

# ==================== 3. STOCK & INVENTAIRE ====================
print("\n📦 Création des catégories de produits...")

inventory_categories_data = [
    'Viandes',
    'Poissons',
    'Légumes',
    'Fruits',
    'Produits laitiers',
    'Épices et condiments',
    'Boissons',
    'Pains et pâtisseries',
]

inv_categories = {}
for cat_name in inventory_categories_data:
    cat, created = InventoryCategory.objects.get_or_create(name=cat_name)
    inv_categories[cat_name] = cat
    print(f"  {'✅' if created else '⏭️ '} Catégorie: {cat.name}")

print("\n🚚 Création des fournisseurs...")

suppliers_data = [
    {'name': 'Boucherie Martin', 'contact_person': 'M. Martin', 'email': 'contact@boucherie-martin.fr', 'phone': '0123456789'},
    {'name': 'Poissonnerie de la Mer', 'contact_person': 'Mme Dupont', 'email': 'info@poissonnerie.fr', 'phone': '0123456790'},
    {'name': 'Fruits & Légumes Bio', 'contact_person': 'M. Bernard', 'email': 'contact@fruitslegumes.fr', 'phone': '0123456791'},
    {'name': 'Laiterie du Terroir', 'contact_person': 'M. Petit', 'email': 'info@laiterie.fr', 'phone': '0123456792'},
]

suppliers = {}
for supp_data in suppliers_data:
    supp, created = Supplier.objects.get_or_create(
        name=supp_data['name'],
        defaults=supp_data
    )
    suppliers[supp_data['name']] = supp
    print(f"  {'✅' if created else '⏭️ '} Fournisseur: {supp.name}")

print("\n🥕 Création des produits...")

products_data = [
    {'name': 'Poulet fermier', 'category': 'Viandes', 'supplier': 'Boucherie Martin', 'unit': 'KG', 'unit_price': 12.50, 'quantity': 50, 'min': 10},
    {'name': 'Bœuf bavette', 'category': 'Viandes', 'supplier': 'Boucherie Martin', 'unit': 'KG', 'unit_price': 18.00, 'quantity': 30, 'min': 5},
    {'name': 'Saumon frais', 'category': 'Poissons', 'supplier': 'Poissonnerie de la Mer', 'unit': 'KG', 'unit_price': 22.00, 'quantity': 20, 'min': 5},
    {'name': 'Crevettes', 'category': 'Poissons', 'supplier': 'Poissonnerie de la Mer', 'unit': 'KG', 'unit_price': 15.00, 'quantity': 15, 'min': 3},
    {'name': 'Tomates', 'category': 'Légumes', 'supplier': 'Fruits & Légumes Bio', 'unit': 'KG', 'unit_price': 3.50, 'quantity': 40, 'min': 10},
    {'name': 'Salade verte', 'category': 'Légumes', 'supplier': 'Fruits & Légumes Bio', 'unit': 'UNIT', 'unit_price': 1.20, 'quantity': 60, 'min': 20},
    {'name': 'Carottes', 'category': 'Légumes', 'supplier': 'Fruits & Légumes Bio', 'unit': 'KG', 'unit_price': 2.50, 'quantity': 35, 'min': 10},
    {'name': 'Pommes de terre', 'category': 'Légumes', 'supplier': 'Fruits & Légumes Bio', 'unit': 'KG', 'unit_price': 1.80, 'quantity': 80, 'min': 20},
    {'name': 'Fromage chèvre', 'category': 'Produits laitiers', 'supplier': 'Laiterie du Terroir', 'unit': 'KG', 'unit_price': 14.00, 'quantity': 10, 'min': 2},
    {'name': 'Crème fraîche', 'category': 'Produits laitiers', 'supplier': 'Laiterie du Terroir', 'unit': 'L', 'unit_price': 4.50, 'quantity': 25, 'min': 5},
    {'name': 'Beurre', 'category': 'Produits laitiers', 'supplier': 'Laiterie du Terroir', 'unit': 'KG', 'unit_price': 8.00, 'quantity': 20, 'min': 5},
    {'name': 'Huile olive', 'category': 'Épices et condiments', 'supplier': 'Fruits & Légumes Bio', 'unit': 'L', 'unit_price': 12.00, 'quantity': 15, 'min': 3},
    {'name': 'Sel', 'category': 'Épices et condiments', 'supplier': 'Fruits & Légumes Bio', 'unit': 'KG', 'unit_price': 2.00, 'quantity': 30, 'min': 5},
    {'name': 'Poivre', 'category': 'Épices et condiments', 'supplier': 'Fruits & Légumes Bio', 'unit': 'KG', 'unit_price': 15.00, 'quantity': 5, 'min': 1},
]

products = {}
product_ref_number = 1
for prod_data in products_data:
    # Générer une référence unique
    reference = f"PROD-{product_ref_number:04d}"

    prod, created = Product.objects.get_or_create(
        reference=reference,
        defaults={
            'name': prod_data['name'],
            'category': inv_categories[prod_data['category']],
            'supplier': suppliers[prod_data['supplier']],
            'unit': prod_data['unit'],
            'unit_price': Decimal(str(prod_data['unit_price'])),
            'quantity_in_stock': Decimal(str(prod_data['quantity'])),
            'minimum_stock': Decimal(str(prod_data['min'])),
        }
    )
    products[prod_data['name']] = prod
    product_ref_number += 1
    print(f"  {'✅' if created else '⏭️ '} Produit: {prod.name}")

# Mouvements de stock
print("\n📊 Création des mouvements de stock...")
for i in range(10):
    product = random.choice(list(products.values()))
    StockMovement.objects.create(
        product=product,
        movement_type='IN',
        quantity=Decimal(str(random.randint(10, 50))),
        unit_price=product.unit_price,
        reference=f'REF-{random.randint(1000, 9999)}',
        reason='Réapprovisionnement automatique'
    )
print(f"  ✅ {StockMovement.objects.count()} mouvements créés")

# ==================== 4. COMPTABILITÉ ====================
print("\n💰 Création des catégories comptables...")

accounting_categories_data = [
    {'name': 'Ventes Restaurant', 'code': '701', 'type': 'REVENUE'},
    {'name': 'Ventes Boissons', 'code': '702', 'type': 'REVENUE'},
    {'name': 'Achats Alimentaires', 'code': '601', 'type': 'EXPENSE'},
    {'name': 'Salaires', 'code': '641', 'type': 'EXPENSE'},
    {'name': 'Loyer', 'code': '613', 'type': 'EXPENSE'},
    {'name': 'Électricité', 'code': '606', 'type': 'EXPENSE'},
]

acc_categories = {}
for cat_data in accounting_categories_data:
    cat, created = AccountCategory.objects.get_or_create(
        code=cat_data['code'],
        defaults={'name': cat_data['name'], 'account_type': cat_data['type']}
    )
    acc_categories[cat_data['name']] = cat
    print(f"  {'✅' if created else '⏭️ '} Catégorie: {cat.name}")

print("\n💳 Création des transactions...")
trans_number = 1
for i in range(30):
    trans_date = today - timedelta(days=random.randint(0, 60))

    # Revenus
    if random.choice([True, False]):
        Transaction.objects.create(
            transaction_number=f'TR-{trans_date.strftime("%Y%m%d")}-{trans_number:04d}',
            category=acc_categories['Ventes Restaurant'],
            transaction_type='INCOME',
            amount=Decimal(str(random.randint(200, 800))),
            date=trans_date,
            description=f'Ventes du {trans_date}',
            payment_method='CARD'
        )
        trans_number += 1

    # Dépenses
    if random.choice([True, False, False]):  # Moins de dépenses
        expense_cat = random.choice([
            acc_categories['Achats Alimentaires'],
            acc_categories['Électricité'],
        ])
        Transaction.objects.create(
            transaction_number=f'TR-{trans_date.strftime("%Y%m%d")}-{trans_number:04d}',
            category=expense_cat,
            transaction_type='EXPENSE',
            amount=Decimal(str(random.randint(100, 500))),
            date=trans_date,
            description=f'Dépense {expense_cat.name}',
            payment_method='BANK_TRANSFER'
        )
        trans_number += 1

print(f"  ✅ {Transaction.objects.count()} transactions créées")

# ==================== 5. RÉSERVATIONS ====================
print("\n🪑 Création des emplacements et tables...")

locations_data = [
    {'name': 'Terrasse', 'description': 'Terrasse extérieure'},
    {'name': 'Salle principale', 'description': 'Salle intérieure principale'},
    {'name': 'Salon privé', 'description': 'Salon pour événements privés'},
]

locations = {}
for loc_data in locations_data:
    loc, created = TableLocation.objects.get_or_create(
        name=loc_data['name'],
        defaults={'description': loc_data['description']}
    )
    locations[loc_data['name']] = loc
    print(f"  {'✅' if created else '⏭️ '} Emplacement: {loc.name}")

print("\n🪑 Création des tables...")
tables = []
table_configs = [
    ('Terrasse', 5, 2),  # 5 tables de 2 personnes
    ('Terrasse', 3, 4),  # 3 tables de 4 personnes
    ('Salle principale', 8, 2),
    ('Salle principale', 6, 4),
    ('Salle principale', 2, 6),
    ('Salon privé', 1, 12),
]

table_number = 1
for loc_name, count, capacity in table_configs:
    for _ in range(count):
        table, created = Table.objects.get_or_create(
            table_number=str(table_number),
            defaults={
                'location': locations[loc_name],
                'capacity': capacity,
            }
        )
        tables.append(table)
        table_number += 1

print(f"  ✅ {len(tables)} tables créées")

print("\n📅 Création des réservations...")
statuses = ['PENDING', 'CONFIRMED', 'COMPLETED', 'CANCELLED']
time_slots = ['12:00', '12:30', '13:00', '19:00', '19:30', '20:00', '20:30']
res_number = 1
reservations_created = 0

# Créer des réservations en évitant les conflits
for i in range(100):  # Essayer de créer jusqu'à 100 fois
    if reservations_created >= 40:
        break

    res_date = today + timedelta(days=random.randint(-15, 15))
    table = random.choice(tables)
    time_slot = random.choice(time_slots)

    # Vérifier si cette combinaison existe déjà
    if not Reservation.objects.filter(
        table=table,
        reservation_date=res_date,
        time_slot=time_slot
    ).exists():
        Reservation.objects.create(
            reservation_number=f'RES-{res_date.strftime("%Y%m%d")}-{res_number:04d}',
            table=table,
            customer_name=random.choice(['Dupont', 'Martin', 'Bernard', 'Petit', 'Dubois', 'Laurent', 'Simon', 'Michel']),
            customer_phone=f'06{random.randint(10000000, 99999999)}',
            customer_email=f'client{reservations_created}@email.com',
            reservation_date=res_date,
            time_slot=time_slot,
            number_of_guests=random.randint(2, 6),
            status=random.choice(statuses),
        )
        res_number += 1
        reservations_created += 1

print(f"  ✅ {Reservation.objects.count()} réservations créées")

# ==================== 6. MENU & COMMANDES ====================
print("\n🍽️ Création des catégories de menu...")

menu_categories_data = [
    {'name': 'Entrées', 'icon': 'fa-leaf', 'order': 1},
    {'name': 'Plats principaux', 'icon': 'fa-drumstick-bite', 'order': 2},
    {'name': 'Desserts', 'icon': 'fa-ice-cream', 'order': 3},
    {'name': 'Boissons', 'icon': 'fa-wine-glass', 'order': 4},
]

menu_categories = {}
for cat_data in menu_categories_data:
    cat, created = MenuCategory.objects.get_or_create(
        name=cat_data['name'],
        defaults={
            'icon': cat_data['icon'],
            'display_order': cat_data['order'],
        }
    )
    menu_categories[cat_data['name']] = cat
    print(f"  {'✅' if created else '⏭️ '} Catégorie menu: {cat.name}")

print("\n🍔 Création des plats...")

menu_items_data = [
    {'name': 'Salade César', 'category': 'Entrées', 'price': 8.50, 'prep_time': 10, 'vegetarian': True},
    {'name': 'Soupe du jour', 'category': 'Entrées', 'price': 6.50, 'prep_time': 5, 'vegetarian': True},
    {'name': 'Carpaccio de bœuf', 'category': 'Entrées', 'price': 12.00, 'prep_time': 10, 'vegetarian': False},

    {'name': 'Poulet rôti', 'category': 'Plats principaux', 'price': 16.50, 'prep_time': 25, 'vegetarian': False},
    {'name': 'Steak frites', 'category': 'Plats principaux', 'price': 18.00, 'prep_time': 20, 'vegetarian': False},
    {'name': 'Saumon grillé', 'category': 'Plats principaux', 'price': 22.00, 'prep_time': 20, 'vegetarian': False},
    {'name': 'Pâtes carbonara', 'category': 'Plats principaux', 'price': 14.00, 'prep_time': 15, 'vegetarian': False},
    {'name': 'Risotto aux légumes', 'category': 'Plats principaux', 'price': 13.50, 'prep_time': 20, 'vegetarian': True},

    {'name': 'Tarte au citron', 'category': 'Desserts', 'price': 6.50, 'prep_time': 5, 'vegetarian': True},
    {'name': 'Mousse au chocolat', 'category': 'Desserts', 'price': 6.00, 'prep_time': 5, 'vegetarian': True},
    {'name': 'Tiramisu', 'category': 'Desserts', 'price': 7.00, 'prep_time': 5, 'vegetarian': True},

    {'name': 'Eau minérale', 'category': 'Boissons', 'price': 3.00, 'prep_time': 1, 'vegetarian': True},
    {'name': 'Coca-Cola', 'category': 'Boissons', 'price': 3.50, 'prep_time': 1, 'vegetarian': True},
    {'name': 'Vin rouge (verre)', 'category': 'Boissons', 'price': 5.00, 'prep_time': 1, 'vegetarian': True},
    {'name': 'Café', 'category': 'Boissons', 'price': 2.50, 'prep_time': 3, 'vegetarian': True},
]

menu_items = {}
for item_data in menu_items_data:
    item, created = MenuItem.objects.get_or_create(
        name=item_data['name'],
        defaults={
            'category': menu_categories[item_data['category']],
            'price': Decimal(str(item_data['price'])),
            'preparation_time': item_data['prep_time'],
            'is_vegetarian': item_data['vegetarian'],
            'is_available': True,
        }
    )
    menu_items[item_data['name']] = item
    print(f"  {'✅' if created else '⏭️ '} Plat: {item.name}")

# Lier quelques ingrédients aux plats
print("\n🥗 Liaison des ingrédients aux plats...")
ingredient_links = [
    ('Salade César', 'Salade verte', 0.2),
    ('Poulet rôti', 'Poulet fermier', 0.3),
    ('Steak frites', 'Bœuf bavette', 0.25),
    ('Steak frites', 'Pommes de terre', 0.3),
    ('Saumon grillé', 'Saumon frais', 0.2),
]

for item_name, product_name, qty in ingredient_links:
    if item_name in menu_items and product_name in products:
        link, created = MenuItemIngredient.objects.get_or_create(
            menu_item=menu_items[item_name],
            product=products[product_name],
            defaults={'quantity_needed': Decimal(str(qty))}
        )
        if created:
            print(f"  ✅ {item_name} → {product_name}")

print("\n🛒 Création des commandes...")
order_types = ['DINE_IN', 'TAKEAWAY', 'DELIVERY']
order_statuses = ['PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'PAID']
customer_names = ['Dupont Jean', 'Martin Pierre', 'Bernard Sophie', 'Petit Thomas', 'Dubois Marie', 'Laurent Alice', 'Simon Marc', 'Michel Julie']

for i in range(50):
    order_date = timezone.now() - timedelta(days=random.randint(0, 30))
    order_type = random.choice(order_types)

    order = Order.objects.create(
        order_number=f'ORD-{order_date.strftime("%Y%m%d")}-{random.randint(1000, 9999)}',
        order_type=order_type,
        table=random.choice(tables) if order_type == 'DINE_IN' else None,
        customer_name=random.choice(customer_names),
        status=random.choice(order_statuses),
        created_by=users['serveur1'],
        order_date=order_date,
    )

    # Ajouter des articles
    num_items = random.randint(2, 5)
    for _ in range(num_items):
        item = random.choice(list(menu_items.values()))
        OrderItem.objects.create(
            order=order,
            menu_item=item,
            quantity=random.randint(1, 3),
            unit_price=item.price,
        )

    # Calculer les totaux
    order.calculate_totals()
    order.save()

    # Créer un ticket de cuisine si commande confirmée
    if order.status in ['CONFIRMED', 'PREPARING', 'READY', 'SERVED', 'PAID']:
        KitchenTicket.objects.get_or_create(
            order=order,
            defaults={
                'ticket_number': f'KT-{order_date.strftime("%Y%m%d")}-{random.randint(100, 999)}',
                'status': 'COMPLETED' if order.status in ['SERVED', 'PAID'] else 'IN_PROGRESS'
            }
        )

print(f"  ✅ {Order.objects.count()} commandes créées")

# ==================== RÉCAPITULATIF ====================
print("\n" + "="*60)
print("🎉 GÉNÉRATION TERMINÉE AVEC SUCCÈS !")
print("="*60)
print(f"\n📊 Récapitulatif des données créées :")
print(f"  👥 Utilisateurs: {User.objects.count()}")
print(f"  🏢 Départements: {Department.objects.count()}")
print(f"  👨‍💼 Employés: {Employee.objects.count()}")
print(f"  📄 Contrats: {Contract.objects.count()}")
print(f"  📅 Présences: {Attendance.objects.count()}")
print(f"  📦 Catégories stock: {InventoryCategory.objects.count()}")
print(f"  🚚 Fournisseurs: {Supplier.objects.count()}")
print(f"  🥕 Produits: {Product.objects.count()}")
print(f"  📊 Mouvements stock: {StockMovement.objects.count()}")
print(f"  💰 Catégories comptables: {AccountCategory.objects.count()}")
print(f"  💳 Transactions: {Transaction.objects.count()}")
print(f"  🪑 Emplacements: {TableLocation.objects.count()}")
print(f"  🪑 Tables: {Table.objects.count()}")
print(f"  📅 Réservations: {Reservation.objects.count()}")
print(f"  🍽️  Catégories menu: {MenuCategory.objects.count()}")
print(f"  🍔 Plats: {MenuItem.objects.count()}")
print(f"  🛒 Commandes: {Order.objects.count()}")
print(f"  🎫 Tickets cuisine: {KitchenTicket.objects.count()}")

print("\n" + "="*60)
print("🔐 IDENTIFIANTS DE CONNEXION :")
print("="*60)
print(f"  • admin        → Mot de passe: admin123")
print(f"  • manager      → Mot de passe: manager123")
print(f"  • chef         → Mot de passe: chef123")
print(f"  • serveur1     → Mot de passe: serveur123")
print(f"  • serveur2     → Mot de passe: serveur123")
print(f"  • cuisinier    → Mot de passe: cuisinier123")

print("\n✅ Vous pouvez maintenant vous connecter et tester le système !")
print("🌐 URL: http://127.0.0.1:8000/accounts/login/")
print("="*60)
