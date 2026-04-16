from django import forms
from .models import Patient


class PatientRegistrationForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            'first_name',
            'last_name',
            'age',
            'gender',
            'blood_group',
            'condition',
            'phone',
            'email',
            'department',
            'medical_history',
            'notes',
            'photo',
            'height',
            'weight',
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Age'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'}),
            'medical_history': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Past Medical History'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Doctor Notes'}),
            'height': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Height in cm'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make these fields required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['age'].required = True
        self.fields['gender'].required = True
        self.fields['blood_group'].required = True
        self.fields['condition'].required = True
        self.fields['phone'].required = True
        self.fields['email'].required = True
        self.fields['department'].required = True
        self.fields['photo'].required = True
        # Keep these optional
        self.fields['medical_history'].required = False
        self.fields['notes'].required = False
        self.fields['height'].required = False
        self.fields['weight'].required = False

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if not photo:
            raise forms.ValidationError("Profile photo is required.")
        return photo