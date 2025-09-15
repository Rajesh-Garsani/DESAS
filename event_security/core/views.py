from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps

# Home page with latest event reviews
def home(request):
    EventReview = apps.get_model('events', 'EventReview')  # dynamic model import
    latest_reviews = EventReview.objects.select_related("event", "registrar").order_by("-created_at")[:6]
    return render(request, "core/home.html", {"latest_reviews": latest_reviews})

# Decorators
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

# Static pages
def about(request):
    return render(request, 'core/about.html')

def unauthorized(request):
    return render(request, 'core/unauthorized.html')

# Contact form with email + lazy-loaded MessageLog
def contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Email to admin
        subject = f"New Contact Form Submission from {name}"
        body = f"Sender: {name}\nEmail: {email}\n\nMessage:\n{message}"

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER],
            fail_silently=False,
        )

        # Lazy import of MessageLog
        MessageLog = apps.get_model('core', 'MessageLog')
        MessageLog.objects.create(
            sender=email,
            recipient=settings.EMAIL_HOST_USER,
            content=body,
            status="received",
            method="email",
            direction="incoming"
        )

        messages.success(request, "Your message has been sent. Our team will contact you soon.")
        return redirect("contact")

    return render(request, "core/contact.html")
