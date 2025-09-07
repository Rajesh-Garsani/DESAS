from django.shortcuts import render, redirect, get_object_or_404
from .models import Event
from .forms import EventForm
from core.decorators import event_registrar_required, admin_required
from accounts.models import CustomUser
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
import datetime
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Event, EventReview
from .forms import EventReviewForm
from django.contrib.auth.decorators import login_required
from .models import EventReview


@event_registrar_required
def dashboard(request):
    events = Event.objects.filter(registrar=request.user).order_by('-datetime')
    context = {
        'events': events,
    }
    return render(request, 'events/dashboard.html', context)


@event_registrar_required
def add_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, user=request.user)
        if form.is_valid():
            event = form.save()
            messages.success(request, 'Event created successfully! Waiting for admin approval.')
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(user=request.user)
    return render(request, 'events/add_event.html', {'form': form})


@event_registrar_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id, registrar=request.user)
    context = {
        'event': event,
        "now": timezone.now(),
    }
    return render(request, 'events/event_detail.html', context)


@admin_required
def manage_events(request):
    events = Event.objects.all().order_by('-datetime')
    context = {
        'events': events,
    }
    return render(request, 'events/manage_events.html', context)


@admin_required
def approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = 'approved'
    event.save()

    # Send notification to event registrar
    subject = f"Event Approved: {event.name}"
    message = f"Your event '{event.name}' scheduled for {event.datetime} has been approved."

    # Email notification
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [event.registrar.email],
        fail_silently=False,
    )

    # SMS notification if phone exists
    if event.registrar.phone:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=event.registrar.phone
            )
            # Log SMS
            MessageLog.objects.create(
                recipient=event.registrar,
                content=message,
                status='sent',
                method='sms'
            )
        except Exception as e:
            MessageLog.objects.create(
                recipient=event.registrar,
                content=message,
                status='failed',
                method='sms'
            )

    # Log email
    MessageLog.objects.create(
        recipient=event.registrar,
        content=message,
        status='sent',
        method='email'
    )

    messages.success(request, 'Event approved successfully! Notification sent.')
    return redirect('manage_events')


@admin_required
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = 'rejected'
    event.save()

    # Send notification to event registrar
    subject = f"Event Rejected: {event.name}"
    message = f"Your event '{event.name}' scheduled for {event.datetime} has been rejected. Please contact support for more information."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [event.registrar.email],
        fail_silently=False,
    )

    # Log email
    MessageLog.objects.create(
        recipient=event.registrar,
        content=message,
        status='sent',
        method='email'
    )

    messages.success(request, 'Event rejected! Notification sent.')
    return redirect('manage_events')


def add_review(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    # Check if event is completed
    if event.datetime > timezone.now():
        messages.error(request, "You can only review after the event is completed.")
        return redirect("dashboard")

    if request.method == "POST":
        form = EventReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.event = event
            review.registrar = request.user
            review.save()
            messages.success(request, "Your review has been submitted.")
            return redirect("event_detail", event_id=event.id)
    else:
        form = EventReviewForm()

    return render(request, "events/add_review.html", {"form": form, "event": event})

@login_required
def review_list(request):
    reviews = EventReview.objects.select_related("event", "registrar").order_by("-created_at")
    return render(request, "events/review_list.html", {"reviews": reviews})