from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class EventRegistrarRegistrationForm(UserCreationForm):
    organization = forms.CharField(max_length=100, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'organization', 'phone')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'event_registrar'
        if commit:
            user.save()
        return user


class SecurityGuardRegistrationForm(UserCreationForm):
    GUARD_TYPE_CHOICES = (
        ('police', 'Police'),
        ('commando', 'Commando'),
        ('security_guard', 'Security Guard'),
    )

    cnic = forms.CharField(max_length=15, required=True, label='CNIC/ID')
    age = forms.IntegerField(required=True, min_value=18, max_value=70)
    experience = forms.IntegerField(required=True, min_value=0, label='Experience (years)')
    guard_type = forms.ChoiceField(choices=GUARD_TYPE_CHOICES, required=True)
    phone = forms.CharField(max_length=15, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'phone', 'cnic', 'age', 'experience', 'guard_type')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'security_guard'
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)