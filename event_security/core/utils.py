from django.core.mail import send_mail
from django.conf import settings
from django.apps import apps
from twilio.rest import Client

def send_notification(subject, body, recipients, phone_numbers=None):
    """Send email and SMS notification + log in MessageLog."""
    # ✅ Lazy import to avoid circular errors
    MessageLog = apps.get_model('core', 'MessageLog')

    # send email
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=False,
    )

    # send SMS if numbers provided
    if phone_numbers and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            for phone in phone_numbers:
                client.messages.create(
                    body=body,
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=phone
                )
        except Exception as e:
            print("SMS failed:", e)

    # log notification
    for r in recipients:
        MessageLog.objects.create(
            recipient=r,
            content=body,      # ✅ fixed: use content instead of message
            status="sent",     # ✅ fixed: lowercase status
            method="email",
            direction="outgoing"
        )
