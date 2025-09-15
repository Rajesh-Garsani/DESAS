from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

from django.utils import timezone

User = get_user_model()


class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ('National & Political Events', 'National & Political Events'),
        ('Religious & Cultural Events', 'Religious & Cultural Events'),
        ('Educational & Academic Events', 'Educational & Academic Events'),
        ('Sports & Entertainment Events', 'Sports & Entertainment Events'),
        ('Social & Corporate Events', 'Social & Corporate Events'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    )

    name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES)
    datetime = models.DateTimeField()
    location = models.CharField(max_length=200)
    crowd_size = models.IntegerField()
    police_count = models.IntegerField(default=0)
    commando_count = models.IntegerField(default=0)
    security_guard_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    registrar = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def total_guards_requested(self):
        return self.police_count + self.commando_count + self.security_guard_count

class EventReview(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="reviews")
    registrar = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    rating = models.IntegerField(default=5, choices=[(i, str(i)) for i in range(1, 6)])  # optional stars 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.registrar} for {self.event.name}"