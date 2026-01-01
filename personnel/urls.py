from django.urls import path
from . import views

app_name = 'personnel'

urlpatterns = [
    # Dashboard
    path('', views.personnel_dashboard, name='dashboard'),

    # Départements
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/<int:pk>/update/', views.department_update, name='department_update'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),

    # Employés
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Contrats
    path('contracts/', views.contract_list, name='contract_list'),
    path('contracts/create/<int:employee_id>/', views.contract_create, name='contract_create'),
    path('contracts/<int:pk>/update/', views.contract_update, name='contract_update'),
    path('contracts/<int:pk>/delete/', views.contract_delete, name='contract_delete'),

    # Présences
    path('attendances/', views.attendance_list, name='attendance_list'),
    path('attendances/create/', views.attendance_create, name='attendance_create'),
    path('attendances/<int:pk>/update/', views.attendance_update, name='attendance_update'),
    path('attendances/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('attendances/bulk-create/', views.attendance_bulk_create, name='attendance_bulk_create'),

    # Congés
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/create/', views.leave_create, name='leave_create'),
    path('leaves/<int:pk>/update/', views.leave_update, name='leave_update'),
    path('leaves/<int:pk>/delete/', views.leave_delete, name='leave_delete'),
    path('leaves/<int:pk>/approve/', views.leave_approve, name='leave_approve'),

    # Fiches de paie
    path('payrolls/', views.payroll_list, name='payroll_list'),
    path('payrolls/create/', views.payroll_create, name='payroll_create'),
    path('payrolls/<int:pk>/', views.payroll_detail, name='payroll_detail'),
    path('payrolls/<int:pk>/update/', views.payroll_update, name='payroll_update'),
    path('payrolls/<int:pk>/delete/', views.payroll_delete, name='payroll_delete'),
    path('payrolls/generate-monthly/', views.payroll_generate_monthly, name='payroll_generate_monthly'),

    # Rapports
    path('reports/', views.personnel_reports, name='reports'),
]