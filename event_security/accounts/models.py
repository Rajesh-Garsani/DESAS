from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('event_registrar', 'Event Registrar'),
        ('security_guard', 'Security Guard'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='event_registrar')
    phone = models.CharField(max_length=15, blank=True, null=True)
    organization = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.username

    def is_admin(self):
        return self.role == 'admin'

    def is_event_registrar(self):
        return self.role == 'event_registrar'

    def is_security_guard(self):
        return self.role == 'security_guard'