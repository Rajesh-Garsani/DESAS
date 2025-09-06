from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

# Add the decorator functions here since we're having issues with core/decorators.py
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to access this page.')
            return redirect('login')
        if not hasattr(request.user, 'is_admin') or not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('unauthorized')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def event_registrar_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to access this page.')
            return redirect('login')
        if not hasattr(request.user, 'is_event_registrar') or not (request.user.is_event_registrar() or request.user.is_admin()):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('unauthorized')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def security_guard_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to access this page.')
            return redirect('login')
        if not hasattr(request.user, 'is_security_guard') or not (request.user.is_security_guard() or request.user.is_admin()):
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('unauthorized')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Now add the actual view functions
def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def contact(request):
    return render(request, 'core/contact.html')

def unauthorized(request):
    return render(request, 'core/unauthorized.html')