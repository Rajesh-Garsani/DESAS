from django.db import models
from django.contrib.auth import get_user_model



from django.core.validators import FileExtensionValidator

User = get_user_model()


class SecurityGuardProfile(models.Model):
    GUARD_TYPE_CHOICES = (
        ('police', 'Police'),
        ('commando', 'Commando'),
        ('security_guard', 'Security Guard'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guard_profile')
    cnic = models.CharField(max_length=15, unique=True)
    age = models.IntegerField()
    experience = models.IntegerField()
    guard_type = models.CharField(max_length=20, choices=GUARD_TYPE_CHOICES)
    is_approved = models.BooleanField(default=False)
    photo = models.ImageField(
        upload_to='guard_photos/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(['jpg', 'jpeg', 'png'])]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_guard_type_display()}"

    def save(self, *args, **kwargs):
        if not self.user.role == 'security_guard':
            self.user.role = 'security_guard'
            self.user.save()
        super().save(*args, **kwargs)


class DutyAssignment(models.Model):
    event = models.ForeignKey('events.Event', on_delete=models.CASCADE, related_name='assignments')
    guards = models.ManyToManyField(
        User,
        limit_choices_to={'role__in': ['police', 'security_guard', 'commando']},
        related_name='duty_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return f"Duty for {self.event.name} ({self.guards.count()} personnel)"
