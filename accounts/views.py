from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import LoginForm, UserRegistrationForm, UserUpdateForm
from .models import User


def login_view(request):
    """Vue de connexion"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Bienvenue {user.get_full_name()} !')
                return redirect('accounts:dashboard')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.info(request, 'Vous avez été déconnecté avec succès.')
    return redirect('accounts:login')


@login_required
def dashboard_view(request):
    """Tableau de bord principal"""
    context = {
        'total_users': User.objects.filter(is_active=True).count(),
        'total_admins': User.objects.filter(role='ADMIN', is_active=True).count(),
        'total_managers': User.objects.filter(role='MANAGER', is_active=True).count(),
        'total_staff': User.objects.filter(is_active=True).exclude(role__in=['ADMIN', 'MANAGER']).count(),
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request):
    """Vue du profil utilisateur"""
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Votre profil a été mis à jour avec succès.')
            return redirect('accounts:profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


class RegisterView(CreateView):
    """Vue d'inscription (accessible uniquement aux admins)"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'Utilisateur créé avec succès.')
        return super().form_valid(form)