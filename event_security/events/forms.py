from django import forms
from .models import Event
from .models import EventReview
from django.utils import timezone




class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'event_type', 'datetime', 'location', 'crowd_size',
                  'police_count', 'commando_count', 'security_guard_count']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        event = super().save(commit=False)
        if self.user:
            event.registrar = self.user
        if commit:
            event.save()
        return event

class EventReviewForm(forms.ModelForm):
    class Meta:
        model = EventReview
        fields = ["message", "rating"]
        widgets = {
            "message": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "rating": forms.Select(attrs={"class": "form-select"}),
        }