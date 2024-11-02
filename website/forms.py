from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import *  # Import your custom User model

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Keep email as required
    first_name = forms.CharField(max_length=30, required=True)  # First name
    last_name = forms.CharField(max_length=30, required=True)  # Last name
    # terms_of_service = forms.BooleanField(required=True, label='I agree to the Terms of Service')
    # privacy_policy = forms.BooleanField(required=True, label='I agree to the Privacy Policy')

    class Meta:
        model = User  # Use your custom User model
        fields = ("username", "first_name", "last_name", "email", "password1", "password2", "role") #, "terms_of_service", "privacy_policy")

    def clean_email(self):
        # This method will be called automatically to clean the email field
        email = self.cleaned_data.get("email")
        if email and not email.endswith('@abdn.ac.uk'):
            raise ValidationError(_('Email must be an @abdn.ac.uk address.'))
        return email

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
class AddMouseForm(forms.ModelForm):
    team = forms.ModelChoiceField(queryset=Team.objects.none(), required=False, label='Select Team')

    class Meta:
        model = Mouse
        fields = [
            'strain', 'tube_id', 'dob', 'sex', 'father', 'mother', 
            'earmark', 'clipped_date', 'state', 'cull_date', 'weaned', 'weaned_date' , 'team'
        ]
        widgets = {
            'tube_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'clipped_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cull_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'weaned_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from the keyword arguments
        super(AddMouseForm, self).__init__(*args, **kwargs)

        # Set the default value for the state field
        self.fields['state'].initial = 'alive'  # Default state to 'alive'
        
        # Limit the father choices to male mice
        self.fields['father'].queryset = Mouse.objects.filter(sex='M')
        
        # Limit the mother choices to female mice
        self.fields['mother'].queryset = Mouse.objects.filter(sex='F')

        # Filter teams based on the current user's memberships
        if user is not None:
            self.fields['team'].queryset = Team.objects.filter(teammembership__user=user)

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']
