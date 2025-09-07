from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.apps import apps
from django.shortcuts import redirect
from .forms import EventRegistrarRegistrationForm, SecurityGuardRegistrationForm, LoginForm
CustomUser = get_user_model()


def register_event_registrar(request):
    if request.method == "POST":
        form = EventRegistrarRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please log in to continue.")
            return redirect("login")   # 👈 send to login page instead of auto login
    else:
        form = EventRegistrarRegistrationForm()
    return render(request, "accounts/register_event_registrar.html", {"form": form})


def register_security_guard(request):
    # Import the SecurityGuardProfile model inside the function to avoid circular imports
    SecurityGuardProfile = apps.get_model('guards', 'SecurityGuardProfile')

    if request.method == 'POST':
        form = SecurityGuardRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()

                # Create guard profile
                SecurityGuardProfile.objects.create(
                    user=user,
                    cnic=form.cleaned_data['cnic'],
                    age=form.cleaned_data['age'],
                    experience=form.cleaned_data['experience'],
                    guard_type=form.cleaned_data['guard_type']
                )

                login(request, user)
                messages.success(request, 'Registration successful! Waiting for admin approval.')
                return redirect('guard_dashboard')
            except Exception as e:
                messages.error(request, f'Error during registration: {str(e)}')
    else:
        form = SecurityGuardRegistrationForm()
    return render(request, 'accounts/register_security_guard.html', {'form': form})


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if user.is_admin():
                    return redirect('admin_dashboard')
                elif user.is_event_registrar():
                    return redirect('dashboard')
                elif user.is_security_guard():
                    return redirect('guard_dashboard')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')