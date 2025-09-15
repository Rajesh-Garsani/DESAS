from django.db import models

class MessageLog(models.Model):
    sender = models.CharField(max_length=255, blank=True, null=True)
    recipient = models.CharField(max_length=255)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=(('sent', 'Sent'), ('failed', 'Failed'), ('received', 'Received'))
    )
    method = models.CharField(
        max_length=10,
        choices=(('email', 'Email'), ('sms', 'SMS'))
    )

    direction = models.CharField(
        max_length=10,
        choices=(('incoming', 'Incoming'), ('outgoing', 'Outgoing'))

    )

    def __str__(self):
        return f"Message to {self.recipient} at {self.sent_at}"
