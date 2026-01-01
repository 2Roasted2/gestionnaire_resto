from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Department, Employee, Contract, Attendance, Leave, Payroll
from .forms import (
    DepartmentForm, EmployeeForm, ContractForm, AttendanceForm,
    LeaveForm, LeaveApprovalForm, PayrollForm, EmployeeSearchForm
)


# Décorateur pour vérifier les permissions
def can_manage_personnel(user):
    return user.is_authenticated and user.can_manage_personnel()


# ==================== DASHBOARD ====================
@login_required
@user_passes_test(can_manage_personnel)
def personnel_dashboard(request):
    """Tableau de bord du module Personnel"""

    # Statistiques générales
    total_employees = Employee.objects.filter(is_active=True).count()
    total_departments = Department.objects.count()

    # Employés par département
    employees_by_dept = Department.objects.annotate(
        employee_count=Count('employees', filter=Q(employees__is_active=True))
    ).values('name', 'employee_count')

    # Employés par rôle
    employees_by_role = Employee.objects.filter(is_active=True).values(
        'user__role'
    ).annotate(count=Count('id'))

    # Congés en attente
    pending_leaves = Leave.objects.filter(status='PENDING').count()

    # Contrats expirant dans 30 jours
    today = timezone.now().date()
    expiring_contracts = Contract.objects.filter(
        is_active=True,
        end_date__isnull=False,
        end_date__lte=today + timedelta(days=30),
        end_date__gte=today
    ).count()

    # Présences du jour
    today_attendances = Attendance.objects.filter(date=today).values('status').annotate(
        count=Count('id')
    )

    # Derniers employés ajoutés
    recent_employees = Employee.objects.filter(is_active=True).order_by('-created_at')[:5]

    # Congés approuvés ce mois
    current_month = timezone.now().month
    current_year = timezone.now().year
    leaves_this_month = Leave.objects.filter(
        start_date__month=current_month,
        start_date__year=current_year,
        status='APPROVED'
    ).count()

    context = {
        'total_employees': total_employees,
        'total_departments': total_departments,
        'employees_by_dept': employees_by_dept,
        'employees_by_role': employees_by_role,
        'pending_leaves': pending_leaves,
        'expiring_contracts': expiring_contracts,
        'today_attendances': today_attendances,
        'recent_employees': recent_employees,
        'leaves_this_month': leaves_this_month,
    }

    return render(request, 'personnel/dashboard.html', context)


# ==================== DÉPARTEMENTS ====================
@login_required
@user_passes_test(can_manage_personnel)
def department_list(request):
    """Liste des départements"""
    departments = Department.objects.all().annotate(
        employee_count=Count('employees', filter=Q(employees__is_active=True))
    )
    return render(request, 'personnel/department_list.html', {'departments': departments})


@login_required
@user_passes_test(can_manage_personnel)
def department_create(request):
    """Créer un département"""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Département créé avec succès.')
            return redirect('personnel:department_list')
    else:
        form = DepartmentForm()

    return render(request, 'personnel/department_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_personnel)
def department_update(request, pk):
    """Modifier un département"""
    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Département modifié avec succès.')
            return redirect('personnel:department_list')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'personnel/department_form.html', {
        'form': form,
        'department': department,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def department_delete(request, pk):
    """Supprimer un département"""
    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Département supprimé avec succès.')
        return redirect('personnel:department_list')

    return render(request, 'personnel/department_confirm_delete.html', {'department': department})


# ==================== EMPLOYÉS ====================
@login_required
@user_passes_test(can_manage_personnel)
def employee_list(request):
    """Liste des employés avec recherche et filtres"""
    employees = Employee.objects.select_related('user', 'department').all()

    # Formulaire de recherche
    search_form = EmployeeSearchForm(request.GET)

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search')
        department = search_form.cleaned_data.get('department')
        is_active = search_form.cleaned_data.get('is_active')

        if search_query:
            employees = employees.filter(
                Q(employee_id__icontains=search_query) |
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query)
            )

        if department:
            employees = employees.filter(department=department)

        if is_active:
            employees = employees.filter(is_active=(is_active == 'true'))

    context = {
        'employees': employees,
        'search_form': search_form,
    }

    return render(request, 'personnel/employee_list.html', context)


@login_required
@user_passes_test(can_manage_personnel)
def employee_detail(request, pk):
    """Détails d'un employé"""
    employee = get_object_or_404(Employee, pk=pk)

    # Contrat actuel
    current_contract = employee.get_current_contract()

    # Tous les contrats
    contracts = employee.contracts.all()

    # Présences du mois en cours
    current_month = timezone.now().month
    current_year = timezone.now().year
    attendances = employee.attendances.filter(
        date__month=current_month,
        date__year=current_year
    ).order_by('-date')

    # Statistiques de présence
    attendance_stats = employee.attendances.filter(
        date__month=current_month,
        date__year=current_year
    ).values('status').annotate(count=Count('id'))

    # Congés
    leaves = employee.leaves.all().order_by('-start_date')[:10]

    # Dernières fiches de paie
    payrolls = employee.payrolls.all().order_by('-year', '-month')[:6]

    context = {
        'employee': employee,
        'current_contract': current_contract,
        'contracts': contracts,
        'attendances': attendances,
        'attendance_stats': attendance_stats,
        'leaves': leaves,
        'payrolls': payrolls,
    }

    return render(request, 'personnel/employee_detail.html', context)


@login_required
@user_passes_test(can_manage_personnel)
def employee_create(request):
    """Créer un employé"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            employee = form.save()
            messages.success(request,
                             f'Employé {employee.user.get_full_name()} créé avec succès. Mot de passe par défaut: password123')
            return redirect('personnel:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm()

    return render(request, 'personnel/employee_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_personnel)
def employee_update(request, pk):
    """Modifier un employé"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeForm(request.POST, request.FILES, instance=employee, user_instance=employee.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Employé modifié avec succès.')
            return redirect('personnel:employee_detail', pk=employee.pk)
    else:
        form = EmployeeForm(instance=employee, user_instance=employee.user)

    return render(request, 'personnel/employee_form.html', {
        'form': form,
        'employee': employee,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def employee_delete(request, pk):
    """Supprimer un employé"""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        user = employee.user
        employee.delete()
        user.delete()
        messages.success(request, 'Employé supprimé avec succès.')
        return redirect('personnel:employee_list')

    return render(request, 'personnel/employee_confirm_delete.html', {'employee': employee})


# Ajoutez ces vues à la suite du fichier personnel/views.py

# ==================== CONTRATS ====================
@login_required
@user_passes_test(can_manage_personnel)
def contract_list(request):
    """Liste de tous les contrats"""
    contracts = Contract.objects.select_related('employee__user').all().order_by('-start_date')
    return render(request, 'personnel/contract_list.html', {'contracts': contracts})


@login_required
@user_passes_test(can_manage_personnel)
def contract_create(request, employee_id):
    """Créer un contrat pour un employé"""
    employee = get_object_or_404(Employee, pk=employee_id)

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES)
        if form.is_valid():
            contract = form.save(commit=False)
            contract.employee = employee
            contract.save()
            messages.success(request, 'Contrat créé avec succès.')
            return redirect('personnel:employee_detail', pk=employee.pk)
    else:
        form = ContractForm()

    return render(request, 'personnel/contract_form.html', {
        'form': form,
        'employee': employee,
        'action': 'Créer'
    })


@login_required
@user_passes_test(can_manage_personnel)
def contract_update(request, pk):
    """Modifier un contrat"""
    contract = get_object_or_404(Contract, pk=pk)

    if request.method == 'POST':
        form = ContractForm(request.POST, request.FILES, instance=contract)
        if form.is_valid():
            form.save()
            messages.success(request, 'Contrat modifié avec succès.')
            return redirect('personnel:employee_detail', pk=contract.employee.pk)
    else:
        form = ContractForm(instance=contract)

    return render(request, 'personnel/contract_form.html', {
        'form': form,
        'contract': contract,
        'employee': contract.employee,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def contract_delete(request, pk):
    """Supprimer un contrat"""
    contract = get_object_or_404(Contract, pk=pk)
    employee = contract.employee

    if request.method == 'POST':
        contract.delete()
        messages.success(request, 'Contrat supprimé avec succès.')
        return redirect('personnel:employee_detail', pk=employee.pk)

    return render(request, 'personnel/contract_confirm_delete.html', {
        'contract': contract,
        'employee': employee
    })


# ==================== PRÉSENCES ====================
@login_required
@user_passes_test(can_manage_personnel)
def attendance_list(request):
    """Liste des présences"""
    # Par défaut, afficher le mois en cours
    today = timezone.now()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    attendances = Attendance.objects.filter(
        date__month=month,
        date__year=year
    ).select_related('employee__user').order_by('-date', 'employee__user__last_name')

    # Statistiques du mois
    stats = attendances.values('status').annotate(count=Count('id'))

    context = {
        'attendances': attendances,
        'stats': stats,
        'current_month': month,
        'current_year': year,
    }

    return render(request, 'personnel/attendance_list.html', context)


@login_required
@user_passes_test(can_manage_personnel)
def attendance_create(request):
    """Créer une présence"""
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save()
            messages.success(request, 'Présence enregistrée avec succès.')
            return redirect('personnel:attendance_list')
    else:
        # Pré-remplir avec la date du jour
        form = AttendanceForm(initial={'date': timezone.now().date()})

    return render(request, 'personnel/attendance_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_personnel)
def attendance_update(request, pk):
    """Modifier une présence"""
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            messages.success(request, 'Présence modifiée avec succès.')
            return redirect('personnel:attendance_list')
    else:
        form = AttendanceForm(instance=attendance)

    return render(request, 'personnel/attendance_form.html', {
        'form': form,
        'attendance': attendance,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def attendance_delete(request, pk):
    """Supprimer une présence"""
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        attendance.delete()
        messages.success(request, 'Présence supprimée avec succès.')
        return redirect('personnel:attendance_list')

    return render(request, 'personnel/attendance_confirm_delete.html', {'attendance': attendance})


@login_required
@user_passes_test(can_manage_personnel)
def attendance_bulk_create(request):
    """Créer des présences en masse pour tous les employés actifs"""
    if request.method == 'POST':
        date = request.POST.get('date')
        status = request.POST.get('status', 'PRESENT')

        if date:
            date_obj = datetime.strptime(date, '%Y-%m-%d').date()
            employees = Employee.objects.filter(is_active=True)

            created_count = 0
            for employee in employees:
                _, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=date_obj,
                    defaults={'status': status}
                )
                if created:
                    created_count += 1

            messages.success(request, f'{created_count} présences créées pour le {date_obj}.')
            return redirect('personnel:attendance_list')

    return render(request, 'personnel/attendance_bulk_create.html', {
        'today': timezone.now().date()
    })


# ==================== CONGÉS ====================
@login_required
@user_passes_test(can_manage_personnel)
def leave_list(request):
    """Liste des congés"""
    leaves = Leave.objects.select_related('employee__user', 'approved_by').all().order_by('-start_date')

    # Filtrer par statut si spécifié
    status_filter = request.GET.get('status')
    if status_filter:
        leaves = leaves.filter(status=status_filter)

    return render(request, 'personnel/leave_list.html', {'leaves': leaves})


@login_required
def leave_create(request):
    """Créer une demande de congé"""
    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES)
        if form.is_valid():
            leave = form.save()
            messages.success(request, 'Demande de congé créée avec succès.')

            if request.user.can_manage_personnel():
                return redirect('personnel:leave_list')
            else:
                return redirect('accounts:dashboard')
    else:
        # Si l'utilisateur n'est pas manager, pré-sélectionner son profil employé
        initial = {}
        if hasattr(request.user, 'employee_profile'):
            initial['employee'] = request.user.employee_profile

        form = LeaveForm(initial=initial)

        # Si pas manager, l'utilisateur ne peut créer que pour lui-même
        if not request.user.can_manage_personnel():
            form.fields['employee'].widget = forms.HiddenInput()

    return render(request, 'personnel/leave_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_personnel)
def leave_update(request, pk):
    """Modifier une demande de congé"""
    leave = get_object_or_404(Leave, pk=pk)

    if request.method == 'POST':
        form = LeaveForm(request.POST, request.FILES, instance=leave)
        if form.is_valid():
            form.save()
            messages.success(request, 'Demande de congé modifiée avec succès.')
            return redirect('personnel:leave_list')
    else:
        form = LeaveForm(instance=leave)

    return render(request, 'personnel/leave_form.html', {
        'form': form,
        'leave': leave,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def leave_delete(request, pk):
    """Supprimer une demande de congé"""
    leave = get_object_or_404(Leave, pk=pk)

    if request.method == 'POST':
        leave.delete()
        messages.success(request, 'Demande de congé supprimée avec succès.')
        return redirect('personnel:leave_list')

    return render(request, 'personnel/leave_confirm_delete.html', {'leave': leave})


@login_required
@user_passes_test(can_manage_personnel)
def leave_approve(request, pk):
    """Approuver/Refuser une demande de congé"""
    leave = get_object_or_404(Leave, pk=pk)

    if request.method == 'POST':
        form = LeaveApprovalForm(request.POST, instance=leave)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.approved_by = request.user
            leave.approved_at = timezone.now()
            leave.save()

            status = leave.get_status_display()
            messages.success(request, f'Demande de congé {status.lower()}e avec succès.')
            return redirect('personnel:leave_list')
    else:
        form = LeaveApprovalForm(instance=leave)

    return render(request, 'personnel/leave_approval.html', {
        'form': form,
        'leave': leave
    })


# ==================== FICHES DE PAIE ====================
@login_required
@user_passes_test(can_manage_personnel)
def payroll_list(request):
    """Liste des fiches de paie"""
    payrolls = Payroll.objects.select_related('employee__user').all().order_by('-year', '-month')

    # Filtrer par année/mois si spécifié
    year = request.GET.get('year')
    month = request.GET.get('month')

    if year:
        payrolls = payrolls.filter(year=year)
    if month:
        payrolls = payrolls.filter(month=month)

    return render(request, 'personnel/payroll_list.html', {'payrolls': payrolls})


@login_required
@user_passes_test(can_manage_personnel)
def payroll_create(request):
    """Créer une fiche de paie"""
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            # Calcul automatique des totaux
            payroll.calculate_totals()
            payroll.save()
            messages.success(request, 'Fiche de paie créée avec succès.')
            return redirect('personnel:payroll_list')
    else:
        # Pré-remplir avec le mois/année en cours
        today = timezone.now()
        form = PayrollForm(initial={
            'month': today.month,
            'year': today.year
        })

    return render(request, 'personnel/payroll_form.html', {'form': form, 'action': 'Créer'})


@login_required
@user_passes_test(can_manage_personnel)
def payroll_update(request, pk):
    """Modifier une fiche de paie"""
    payroll = get_object_or_404(Payroll, pk=pk)

    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.calculate_totals()
            payroll.save()
            messages.success(request, 'Fiche de paie modifiée avec succès.')
            return redirect('personnel:payroll_list')
    else:
        form = PayrollForm(instance=payroll)

    return render(request, 'personnel/payroll_form.html', {
        'form': form,
        'payroll': payroll,
        'action': 'Modifier'
    })


@login_required
@user_passes_test(can_manage_personnel)
def payroll_delete(request, pk):
    """Supprimer une fiche de paie"""
    payroll = get_object_or_404(Payroll, pk=pk)

    if request.method == 'POST':
        payroll.delete()
        messages.success(request, 'Fiche de paie supprimée avec succès.')
        return redirect('personnel:payroll_list')

    return render(request, 'personnel/payroll_confirm_delete.html', {'payroll': payroll})


@login_required
@user_passes_test(can_manage_personnel)
def payroll_detail(request, pk):
    """Détails d'une fiche de paie"""
    payroll = get_object_or_404(Payroll, pk=pk)
    return render(request, 'personnel/payroll_detail.html', {'payroll': payroll})


@login_required
@user_passes_test(can_manage_personnel)
def payroll_generate_monthly(request):
    """Générer les fiches de paie pour tous les employés actifs du mois"""
    if request.method == 'POST':
        month = int(request.POST.get('month'))
        year = int(request.POST.get('year'))

        employees = Employee.objects.filter(is_active=True)
        created_count = 0

        for employee in employees:
            # Vérifier si une fiche existe déjà
            if not Payroll.objects.filter(employee=employee, month=month, year=year).exists():
                # Récupérer le contrat actuel
                contract = employee.get_current_contract()

                if contract:
                    # Calculer les présences du mois
                    attendances = Attendance.objects.filter(
                        employee=employee,
                        date__month=month,
                        date__year=year,
                        status='PRESENT'
                    )

                    total_hours = attendances.aggregate(
                        total=Sum('hours_worked')
                    )['total'] or 0

                    # Calculer les absences
                    absences = Attendance.objects.filter(
                        employee=employee,
                        date__month=month,
                        date__year=year,
                        status='ABSENT'
                    ).count()

                    # Calcul simplifié
                    base_salary = contract.base_salary
                    allowances = contract.meal_allowance * 22 + contract.transport_allowance

                    # Déduction pour absences (1 jour = base_salary / 30)
                    absences_deduction = (base_salary / 30) * absences

                    # Cotisations sociales (~22% du brut)
                    gross = base_salary + allowances - absences_deduction
                    social_security = gross * Decimal('0.22')

                    # Créer la fiche de paie
                    payroll = Payroll.objects.create(
                        employee=employee,
                        month=month,
                        year=year,
                        base_salary=base_salary,
                        overtime_hours=0,
                        overtime_amount=0,
                        bonuses=0,
                        allowances=allowances,
                        absences_deduction=absences_deduction,
                        social_security=social_security,
                        tax=0,
                        other_deductions=0
                    )

                    payroll.calculate_totals()
                    payroll.save()
                    created_count += 1

        messages.success(request, f'{created_count} fiches de paie générées pour {month}/{year}.')
        return redirect('personnel:payroll_list')

    # Afficher le formulaire
    today = timezone.now()
    return render(request, 'personnel/payroll_generate_monthly.html', {
        'current_month': today.month,
        'current_year': today.year
    })


# ==================== RAPPORTS ET STATISTIQUES ====================
@login_required
@user_passes_test(can_manage_personnel)
def personnel_reports(request):
    """Page de rapports et statistiques"""

    # Statistiques générales
    total_employees = Employee.objects.filter(is_active=True).count()

    # Répartition par département
    dept_stats = Department.objects.annotate(
        count=Count('employees', filter=Q(employees__is_active=True))
    ).values('name', 'count')

    # Répartition par genre
    gender_stats = Employee.objects.filter(is_active=True).values('gender').annotate(
        count=Count('id')
    )

    # Masse salariale mensuelle
    current_month = timezone.now().month
    current_year = timezone.now().year

    payroll_stats = Payroll.objects.filter(
        month=current_month,
        year=current_year
    ).aggregate(
        total_gross=Sum('gross_salary'),
        total_net=Sum('net_salary'),
        avg_salary=Avg('net_salary')
    )

    # Taux de présence du mois
    total_days = Attendance.objects.filter(
        date__month=current_month,
        date__year=current_year
    ).count()

    present_days = Attendance.objects.filter(
        date__month=current_month,
        date__year=current_year,
        status='PRESENT'
    ).count()

    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0

    # Congés du mois
    leaves_stats = Leave.objects.filter(
        start_date__month=current_month,
        start_date__year=current_year
    ).values('status').annotate(count=Count('id'))

    context = {
        'total_employees': total_employees,
        'dept_stats': dept_stats,
        'gender_stats': gender_stats,
        'payroll_stats': payroll_stats,
        'attendance_rate': round(attendance_rate, 2),
        'leaves_stats': leaves_stats,
        'current_month': current_month,
        'current_year': current_year,
    }

    return render(request, 'personnel/reports.html', context)