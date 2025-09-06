from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MessageLog(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=(('sent', 'Sent'), ('failed', 'Failed')))
    method = models.CharField(max_length=10, choices=(('email', 'Email'), ('sms', 'SMS')))

    def __str__(self):
        return f"Message to {self.recipient.username} at {self.sent_at}"