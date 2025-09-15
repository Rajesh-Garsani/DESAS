from django import forms
from .models import SecurityGuardProfile

class GuardProfileForm(forms.ModelForm):
    class Meta:
        model = SecurityGuardProfile
        fields = ['cnic', 'age', 'experience', 'guard_type']