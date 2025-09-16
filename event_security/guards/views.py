from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.apps import apps
from django.conf import settings
from django.core.mail import send_mail
from .models import SecurityGuardProfile, DutyAssignment
from .forms import GuardProfileForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone

from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter





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


# Import other models using Django's app registry to avoid circular imports
def get_event_model():
    return apps.get_model('events', 'Event')


def get_message_log_model():
    return apps.get_model('core', 'MessageLog')


# Import Twilio only if needed to avoid errors if not installed
try:
    from twilio.rest import Client

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False


@security_guard_required
def guard_dashboard(request):
    # DutyAssignment uses a ManyToManyField 'guards'
    assignments = DutyAssignment.objects.filter(guards=request.user).select_related('event')

    is_approved = False
    try:
        is_approved = request.user.guard_profile.is_approved
    except SecurityGuardProfile.DoesNotExist:
        pass

    context = {
        'assignments': assignments,
        'is_approved': is_approved
    }
    return render(request, 'guards/dashboard.html', context)


@security_guard_required
def edit_profile(request):
    try:
        guard_profile = SecurityGuardProfile.objects.get(user=request.user)
    except SecurityGuardProfile.DoesNotExist:
        guard_profile = SecurityGuardProfile(user=request.user)
        guard_profile.save()

    if request.method == 'POST':
        form = GuardProfileForm(request.POST, instance=guard_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('guard_dashboard')
    else:
        form = GuardProfileForm(instance=guard_profile)

    context = {
        'form': form,
    }
    return render(request, 'guards/edit_profile.html', context)


@security_guard_required
def assignments(request):
    assignments = DutyAssignment.objects.filter(guards=request.user).select_related('event')
    return render(request, 'guards/assignments.html', {'assignments': assignments})


@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(DutyAssignment, id=assignment_id, guards=request.user)
    return render(request, 'guards/assignment_detail.html', {'assignment': assignment})

@admin_required
def manage_guards(request):
    User = get_user_model()
    guards = User.objects.filter(role='security_guard')

    # Add profile information to each guard
    guard_profiles = []
    for guard in guards:
        try:
            profile = SecurityGuardProfile.objects.get(user=guard)
            guard_profiles.append({
                'user': guard,
                'profile': profile
            })
        except SecurityGuardProfile.DoesNotExist:
            guard_profiles.append({
                'user': guard,
                'profile': None
            })

    context = {
        'guard_profiles': guard_profiles,
    }
    return render(request, 'guards/manage_guards.html', context)


@admin_required
def approve_guard(request, guard_id):
    User = get_user_model()
    guard = get_object_or_404(User, id=guard_id, role='security_guard')

    try:
        profile = SecurityGuardProfile.objects.get(user=guard)
    except SecurityGuardProfile.DoesNotExist:
        profile = SecurityGuardProfile(user=guard)

    profile.is_approved = True
    profile.save()

    messages.success(request, f'{guard.username} has been approved as a security guard.')
    return redirect('manage_guards')


@admin_required
def reject_guard(request, guard_id):
    User = get_user_model()
    guard = get_object_or_404(User, id=guard_id, role='security_guard')
    guard.delete()

    messages.success(request, f'User {guard.username} has been rejected and removed from the system.')
    return redirect('manage_guards')


@admin_required
def assign_duty(request):
    Event = get_event_model()
    User = get_user_model()
    MessageLog = get_message_log_model()

    if request.method == 'POST':
        event_id = request.POST.get('event')
        guard_ids = request.POST.getlist('guards')

        event = get_object_or_404(Event, id=event_id)
        guards = User.objects.filter(id__in=guard_ids, role='security_guard')

        for guard in guards:
            assignment, created = DutyAssignment.objects.get_or_create(event=event, guard=guard)

            # Send notification to guard
            subject = f"New Duty Assignment: {event.name}"
            message = f"You have been assigned to duty at {event.name} on {event.datetime} at {event.location}."

            # ✅ Email notification
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [guard.email],
                    fail_silently=False,
                )
                email_status = "sent"
            except Exception:
                email_status = "failed"

            # ✅ Log email
            MessageLog.objects.create(
                sender=settings.DEFAULT_FROM_EMAIL,
                recipient=guard.email,
                content=message,
                status=email_status,
                method="email",
                direction="outgoing"
            )

            # ✅ SMS notification if phone exists and Twilio is available
            if guard.phone and TWILIO_AVAILABLE:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(
                        body=message,
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to=guard.phone
                    )
                    sms_status = "sent"
                except Exception:
                    sms_status = "failed"

                # ✅ Log SMS
                MessageLog.objects.create(
                    sender=settings.TWILIO_PHONE_NUMBER,
                    recipient=guard.phone,
                    content=message,
                    status=sms_status,
                    method="sms",
                    direction="outgoing"
                )

        event.status = 'assigned'
        event.save()

        messages.success(request, f'Duties assigned successfully! Notifications sent to {guards.count()} guards.')
        return redirect('assign_duty')

    # GET request
    events = Event.objects.filter(status='approved')
    guards = User.objects.filter(role='security_guard')

    # Add profile information to each guard
    guard_profiles = []
    for guard in guards:
        try:
            profile = SecurityGuardProfile.objects.get(user=guard)
            if profile.is_approved:
                guard_profiles.append({
                    'user': guard,
                    'profile': profile
                })
        except SecurityGuardProfile.DoesNotExist:
            pass

    context = {
        'events': events,
        'guards': guard_profiles,
    }
    return render(request, 'guards/assign_duty.html', context)



@admin_required
def admin_dashboard(request):
    Event = get_event_model()
    User = get_user_model()

    total_events = Event.objects.count()
    total_guards = User.objects.filter(role='security_guard').count()
    pending_events = Event.objects.filter(status='pending').count()

    # Count approved guards
    approved_guards = 0
    guards = User.objects.filter(role='security_guard')
    for guard in guards:
        try:
            if SecurityGuardProfile.objects.get(user=guard).is_approved:
                approved_guards += 1
        except SecurityGuardProfile.DoesNotExist:
            pass

    pending_guards = total_guards - approved_guards

    context = {
        'total_events': total_events,
        'total_guards': total_guards,
        'approved_guards': approved_guards,
        'pending_events': pending_events,
        'pending_guards': pending_guards,
    }
    return render(request, 'admin/admin_dashboard.html', context)


@admin_required
def messages_log(request):
    MessageLog = get_message_log_model()
    logs = MessageLog.objects.all().order_by('-sent_at')
    context = {
        'logs': logs,
    }
    return render(request, 'admin/messages_log.html', context)



@security_guard_required
def reject_assignment(request, assignment_id):
    assignment = get_object_or_404(DutyAssignment, id=assignment_id, guards=request.user)

    if request.method == "POST":
        reason = request.POST.get("reason", "No reason provided")
        assignment.details = f"Rejected: {reason}"
        assignment.save()

        # ✅ Create log entry
        MessageLog = get_message_log_model()
        MessageLog.objects.create(
            recipient="Admin",
            content=f"Guard {request.user.username} rejected assignment for event {assignment.event.name}. Reason: {reason}",
            status="info",
            method="system",
            direction="incoming"
        )

        # ✅ Send email to admin
        send_mail(
            subject=f"Assignment Rejected - {assignment.event.name}",
            message=f"Guard {request.user.username} rejected assignment for event '{assignment.event.name}'.\nReason: {reason}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # admin email
            fail_silently=False,
        )

        messages.success(request, "You have rejected this assignment.")
        return redirect("guard_dashboard")

    return render(request, "guards/reject_assignment.html", {"assignment": assignment})


@security_guard_required
def complete_assignment(request, assignment_id):
    assignment = get_object_or_404(DutyAssignment, id=assignment_id, guards=request.user)

    assignment.details = "Completed successfully"
    assignment.assigned_at = timezone.now()
    assignment.save()

    # ✅ Create log entry
    MessageLog = get_message_log_model()
    MessageLog.objects.create(
        recipient="Admin",
        content=f"Guard {request.user.username} marked assignment for event {assignment.event.name} as completed.",
        status="info",
        method="system",
        direction="incoming"
    )

    # ✅ Send email to admin
    send_mail(
        subject=f"Assignment Completed - {assignment.event.name}",
        message=f"Guard {request.user.username} has marked assignment for event '{assignment.event.name}' as completed.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.DEFAULT_FROM_EMAIL],  # admin email
        fail_silently=False,
    )

    messages.success(request, "You have marked this assignment as completed.")
    return redirect("guard_dashboard")


@login_required
@security_guard_required
def guard_history(request):
    assignments = DutyAssignment.objects.filter(guards=request.user).select_related("event")

    completed_logs = []
    rejected_logs = []

    # Fetch completion & rejection from MessageLog (if you are saving them there)
    MessageLog = get_message_log_model()
    if MessageLog:
        completed_logs = MessageLog.objects.filter(
            recipient=request.user.email,
            content__icontains="completed duty"
        ).order_by("-sent_at")

        rejected_logs = MessageLog.objects.filter(
            recipient=request.user.email,
            content__icontains="rejected"
        ).order_by("-sent_at")

    context = {
        "assignments": assignments,
        "completed_logs": completed_logs,
        "rejected_logs": rejected_logs,
    }
    return render(request, "guards/history.html", context)


@login_required
@security_guard_required
def export_guard_history_pdf(request):
    assignments = DutyAssignment.objects.filter(guards=request.user).select_related("event")

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="guard_history_{request.user.username}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, height - 50, "DESAS - Guard Duty History")

    # Guard Info
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 100, f"Guard: {request.user.username}")
    p.drawString(50, height - 120, f"Email: {request.user.email}")
    if hasattr(request.user, "phone"):
        p.drawString(50, height - 140, f"Phone: {request.user.phone}")

    y = height - 180
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Assigned Duties:")
    y -= 30

    # List assignments
    p.setFont("Helvetica", 11)
    for assignment in assignments:
        text = f"{assignment.event.name} - {assignment.event.datetime} at {assignment.event.location}"
        p.drawString(60, y, text)
        y -= 20
        if y < 100:  # New page if too long
            p.showPage()
            y = height - 50

    # Footer
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 40, f"Generated by DESAS on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")

    p.save()
    return response