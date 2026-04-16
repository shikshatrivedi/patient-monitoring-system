from django import forms
from django.contrib.auth.models import User
from .models import DoctorProfile
from django.core.exceptions import ValidationError
import re

class RegistrationForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    degree = forms.CharField(required=False)
    mobile_number = forms.CharField(required=False)
    department = forms.CharField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    id_card = forms.FileField(
        required=True,
        help_text="Upload your Doctor ID Card (image or PDF)"
    )

    def clean_password(self):
        password = self.cleaned_data.get("password")
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?]).{8,}$'
        if password and not re.match(pattern, password):
            raise forms.ValidationError(
                "Password must be at least 8 characters and include uppercase, lowercase, number, and special character."
            )
        return password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-input'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'}))