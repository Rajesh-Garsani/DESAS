import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.apps import apps
from django.contrib.auth.decorators import login_required
from .models import Event, EventReview
from .forms import EventForm, EventReviewForm
import io
from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa
from django.shortcuts import get_object_or_404, redirect




# ✅ Lazy imports for decorators
try:
    from core.decorators import event_registrar_required, admin_required
except ImportError:
    def event_registrar_required(view_func):
        return view_func
    def admin_required(view_func):
        return view_func

# ✅ Lazy import for CustomUser (avoid direct import issues)
def get_user_model():
    return apps.get_model("accounts", "CustomUser")

# ✅ Lazy import for MessageLog
def get_message_log_model():
    return apps.get_model("core", "MessageLog")

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

logger = logging.getLogger(__name__)



@event_registrar_required
def dashboard(request):
    events = Event.objects.filter(registrar=request.user).order_by('-datetime')

    # Get DutyAssignment model lazily
    DutyAssignment = apps.get_model('guards', 'DutyAssignment')

    # Build a mapping event_id -> queryset of guards
    event_assignments = {}
    # fetch assignments for these events and prefetch guards
    assignments = DutyAssignment.objects.filter(event__in=events).prefetch_related('guards')
    for a in assignments:
        event_assignments.setdefault(a.event_id, []).extend(list(a.guards.all()))

    return render(request, 'events/dashboard.html', {
        'events': events,
        'event_assignments': event_assignments,
    })


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

    DutyAssignment = apps.get_model('guards', 'DutyAssignment')
    assignments = DutyAssignment.objects.filter(event=event).prefetch_related('guards')

    # gather guards (deduplicate)
    guards = []
    seen = set()
    for a in assignments:
        for g in a.guards.all():
            if g.pk not in seen:
                guards.append(g)
                seen.add(g.pk)

    # optionally fetch logs for registrar if you want (keeps your previous behavior)
    MessageLog = apps.get_model('core', 'MessageLog')
    logs = MessageLog.objects.filter(recipient=event.registrar.email).order_by('-sent_at')

    return render(request, 'events/event_detail.html', {
        'event': event,
        'guards': guards,
        'logs': logs,
        'now': timezone.now(),
    })


@admin_required
def manage_events(request):
    events = Event.objects.all().order_by('-datetime')
    return render(request, 'events/manage_events.html', {'events': events})


@admin_required
def approve_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = 'approved'
    event.save()

    subject = f"Event Approved: {event.name}"
    message = f"Your event '{event.name}' scheduled for {event.datetime} has been approved."

    # ✅ Email
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [event.registrar.email],
        fail_silently=False,
    )

    # ✅ Log email
    MessageLog = get_message_log_model()
    MessageLog.objects.create(
        sender=settings.DEFAULT_FROM_EMAIL,
        recipient=event.registrar.email,
        content=message,
        status="sent",
        method="email",
        direction="outgoing"
    )

    # ✅ SMS if Twilio is available
    if getattr(event.registrar, "phone", None) and TWILIO_AVAILABLE:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=event.registrar.phone
            )
            sms_status = "sent"
        except Exception:
            sms_status = "failed"

        MessageLog.objects.create(
            sender=settings.TWILIO_PHONE_NUMBER,
            recipient=event.registrar.phone,
            content=message,
            status=sms_status,
            method="sms",
            direction="outgoing"
        )

    messages.success(request, 'Event approved successfully! Notification sent.')
    return redirect('manage_events')


@admin_required
def reject_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.status = 'rejected'
    event.save()

    subject = f"Event Rejected: {event.name}"
    message = f"Your event '{event.name}' scheduled for {event.datetime} has been rejected. Please contact support."

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [event.registrar.email],
        fail_silently=False,
    )

    MessageLog = get_message_log_model()
    MessageLog.objects.create(
        sender=settings.DEFAULT_FROM_EMAIL,
        recipient=event.registrar.email,
        content=message,
        status="sent",
        method="email",
        direction="outgoing"
    )

    messages.success(request, "Event rejected! Notification sent.")
    return redirect('manage_events')




def add_review(request, event_id):
    event = get_object_or_404(Event, id=event_id)

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




def export_event_pdf(request, event_id):
    """
    Export a PDF with event details and assigned guards.
    Only allowed for the event registrar or admin users.
    """
    # load Event model (already imported at top of file in many versions)
    try:
        Event = apps.get_model('events', 'Event')
    except Exception:
        # fallback if Event is already imported at file top
        from .models import Event

    event = get_object_or_404(Event, id=event_id)

    # Permission: only event.registrar or admin allowed
    user = request.user
    is_admin = hasattr(user, 'is_admin') and user.is_admin() if user.is_authenticated else False
    if not user.is_authenticated:
        messages.error(request, "Please login to download event PDF.")
        return redirect('login')

    if not (user == event.registrar or is_admin):
        messages.error(request, "You do not have permission to download this event PDF.")
        return redirect('unauthorized')

    # Get assigned guards (DutyAssignment -> guards)
    DutyAssignment = apps.get_model('guards', 'DutyAssignment')
    assignments = DutyAssignment.objects.filter(event=event).prefetch_related('guards')
    guards = []
    seen = set()
    for a in assignments:
        for g in a.guards.all():
            if g.pk not in seen:
                guards.append(g)
                seen.add(g.pk)

    # Render HTML from template
    context = {
        'event': event,
        'guards': guards,
        'now': timezone.now(),
    }
    html = render_to_string('events/event_pdf.html', context)

    # Convert HTML to PDF
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(src=html, dest=result)

    if pisa_status.err:
        # Return plain html on error so you can debug
        return HttpResponse('We had some errors generating the PDF. <pre>{}</pre>'.format(pisa_status.err), content_type='text/html')

    # Build response
    filename = f"{event.name}_details.pdf".replace(' ', '_')
    response = HttpResponse(result.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response