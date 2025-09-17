from django.contrib import admin, messages
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
from django.utils.html import format_html

# Twilio optional
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False

from django.contrib.auth import get_user_model
from .models import SecurityGuardProfile, DutyAssignment

User = get_user_model()




@admin.register(SecurityGuardProfile)
class SecurityGuardProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_guard_type_display_short', 'cnic', 'age', 'experience', 'is_approved', 'photo_thumbnail')
    list_filter = ('guard_type', 'is_approved')
    search_fields = ('user__username', 'cnic')

    def get_guard_type_display_short(self, obj):
        return obj.get_guard_type_display()
    get_guard_type_display_short.short_description = 'Guard Type'

    def photo_thumbnail(self, obj):
        if obj.photo:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;" />', obj.photo.url)
        return "-"
    photo_thumbnail.short_description = 'Photo'



@admin.register(DutyAssignment)
class DutyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('event', 'get_guards', 'assigned_at')
    filter_horizontal = ('guards',)           # <-- dual-pane multi-select widget
    search_fields = ('event__name', 'guards__username')
    list_filter = ('event',)

    def get_guards(self, obj):
        return ", ".join([g.username for g in obj.guards.all()])
    get_guards.short_description = "Assigned Guards"

    # keep the existing save_model/save_related pattern if you have notifications;
    # if you don't need notifications here, you can omit save_model/save_related.
    def save_model(self, request, obj, form, change):
        if obj.pk:
            obj._old_guard_pks = set(obj.guards.all().values_list('pk', flat=True))
        else:
            obj._old_guard_pks = set()
        super().save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        new_guard_pks = set(obj.guards.all().values_list('pk', flat=True))
        old_guard_pks = getattr(obj, '_old_guard_pks', set())
        added_pks = new_guard_pks - old_guard_pks
        if not added_pks:
            return

        MessageLog = apps.get_model('core', 'MessageLog')

        for guard in obj.guards.filter(pk__in=added_pks):
            subject = f"New Duty Assignment: {obj.event.name}"
            message = f"You have been assigned to duty at {obj.event.name} on {obj.event.datetime} at {obj.event.location}."

            # email
            recipient_email = getattr(guard, 'email', None)
            email_status = None
            if recipient_email:
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
                    email_status = 'sent'
                except Exception:
                    email_status = 'failed'
                try:
                    MessageLog.objects.create(
                        sender=settings.DEFAULT_FROM_EMAIL,
                        recipient=recipient_email,
                        content=message,
                        status=email_status or 'failed',
                        method='email',
                        direction='outgoing'
                    )
                except Exception:
                    pass

            # sms
            recipient_phone = getattr(guard, 'phone', None)
            sms_status = None
            if recipient_phone and TWILIO_AVAILABLE:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=recipient_phone)
                    sms_status = 'sent'
                except Exception:
                    sms_status = 'failed'
                try:
                    MessageLog.objects.create(
                        sender=settings.TWILIO_PHONE_NUMBER,
                        recipient=recipient_phone,
                        content=message,
                        status=sms_status or 'failed',
                        method='sms',
                        direction='outgoing'
                    )
                except Exception:
                    pass

        messages.success(request, f"Notifications attempted for {len(added_pks)} newly assigned guards.")
