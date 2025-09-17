from django import forms
from .models import SecurityGuardProfile

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

class GuardProfileForm(forms.ModelForm):
    class Meta:
        model = SecurityGuardProfile
        fields = ['cnic', 'age', 'experience', 'guard_type', 'photo']
        widgets = {
            'guard_type': forms.Select(),
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo:
            if photo.size > MAX_IMAGE_SIZE:
                raise forms.ValidationError("Image file too large ( > 5MB ). Please choose a smaller image.")
        return photo
