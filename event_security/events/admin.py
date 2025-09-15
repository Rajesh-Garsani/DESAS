from django.contrib import admin, messages
from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps

# Twilio optional
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except Exception:
    TWILIO_AVAILABLE = False

from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'datetime', 'registrar', 'status')
    list_filter = ('status',)
    search_fields = ('name', 'registrar__username')

    def save_model(self, request, obj, form, change):
        # capture old status (None if new)
        old_status = None
        if obj.pk:
            try:
                old_status = Event.objects.get(pk=obj.pk).status
            except Event.DoesNotExist:
                old_status = None

        # save the model (this updates the DB)
        super().save_model(request, obj, form, change)

        # if status changed, send notifications for approved/rejected
        if old_status != obj.status:
            # only send notifications on these statuses (adjust if you want others)
            if obj.status == 'approved':
                subject = f"Event Approved: {obj.name}"
                message = f"Your event '{obj.name}' scheduled for {obj.datetime} has been approved."
            elif obj.status == 'rejected':
                subject = f"Event Rejected: {obj.name}"
                message = f"Your event '{obj.name}' scheduled for {obj.datetime} has been rejected. Please contact support for more information."
            else:
                # no notifications for other status changes
                return

            # recipients & phones (guards/registrar fields may vary — use attributes carefully)
            recipient_email = getattr(obj.registrar, 'email', None)
            recipient_phone = getattr(obj.registrar, 'phone', None)

            # lazy load MessageLog model (avoid circular import)
            MessageLog = apps.get_model('core', 'MessageLog')

            # send email
            email_status = None
            if recipient_email:
                try:
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email], fail_silently=False)
                    email_status = 'sent'
                except Exception as e:
                    email_status = 'failed'

                # log the email
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
                    # don't raise in admin save — just continue
                    pass

            # send SMS if Twilio configured
            sms_status = None
            if recipient_phone and TWILIO_AVAILABLE:
                try:
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=recipient_phone)
                    sms_status = 'sent'
                except Exception:
                    sms_status = 'failed'

                # log the SMS
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

            # Feedback to admin user (optional, helpful)
            messages.success(request, f"Notifications attempted. Email: {email_status}, SMS: {sms_status if recipient_phone else 'not sent (no number)'}")
