from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

from django.apps import apps   # ✅ to safely get models






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
    phone = forms.CharField(max_length=11, required=True)
    photo = forms.ImageField(required=True, label="Profile Photo")  # ✅ keep as extra form field

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'password1', 'password2', 'phone',
            'cnic', 'age', 'experience', 'guard_type'
        )  # ❌ photo removed here

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'security_guard'
        if commit:
            user.save()
            # Link SecurityGuardProfile
            SecurityGuardProfile = apps.get_model('guards', 'SecurityGuardProfile')
            SecurityGuardProfile.objects.create(
                user=user,
                cnic=self.cleaned_data['cnic'],
                age=self.cleaned_data['age'],
                experience=self.cleaned_data['experience'],
                guard_type=self.cleaned_data['guard_type'],
                photo=self.cleaned_data.get('photo')  # ✅ assign uploaded file
            )
        return user





class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)