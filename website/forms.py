from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import *  # Import your custom User model


class UserPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super(UserPasswordResetForm, self).__init__(*args, **kwargs)

    email = forms.EmailField(label='', widget=forms.EmailInput(attrs={
        'class': 'your-class',
        'placeholder': 'Enter your email address',
        'type': 'email',
        'name': 'email'
    }))

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Keep email as required
    first_name = forms.CharField(max_length=30, required=True)  # First name
    last_name = forms.CharField(max_length=30, required=True)  # Last name
    # terms_of_service = forms.BooleanField(required=True, label='I agree to the Terms of Service')
    # privacy_policy = forms.BooleanField(required=True, label='I agree to the Privacy Policy')

    class Meta:
        model = User  # Use your custom User model
        fields = ("profile_picture", "username", "first_name", "last_name", "email", "password1", "password2", "role") #, "terms_of_service", "privacy_policy")

    def clean_email(self):
        # This method will be called automatically to clean the email field
        email = self.cleaned_data.get("email")
        if email and not email.endswith('@abdn.ac.uk'):
            raise ValidationError(_('Email must be an @abdn.ac.uk address.'))
        
        # Check if the email already exists in the database
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('This email address is already in use.'))
        
        return email

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['profile_picture', 'username', 'first_name', 'last_name']
    
class AddMouseForm(forms.ModelForm):
    team = forms.ModelChoiceField(queryset=Team.objects.none(), required=False, label='Select Team')
    earmark = forms.MultipleChoiceField(
        choices=Mouse.CLIPPED_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Earmark (Clipping)'
    )
    strain = forms.ModelChoiceField(queryset=Strain.objects.all(), required=False, label='Select Strain')
    new_strain = forms.CharField(max_length=100, required=False, label='New Strain')
    genotype = forms.ModelChoiceField(queryset=Mouse.GENOTYPE_CHOICES, required=False, label="Select genotype")

    class Meta:
        model = Mouse
        fields = [
            'strain', 'tube_id', 'dob', 'sex', 'father', 'mother', 
            'earmark', 'clipped_date', 'state', 'cull_date', 'weaned', 'weaned_date' , 'team' , 'genotype'
        ]
        widgets = {
            'tube_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'sex': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'clipped_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cull_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'weaned_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean_earmark(self):
        """Clean earmark data and convert it to a comma-separated string."""
        earmark_choices = self.cleaned_data.get('earmark', [])
        return earmark_choices

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  # Get the user from the keyword arguments
        super(AddMouseForm, self).__init__(*args, **kwargs)

        # Set the default value for the state field
        self.fields['state'].initial = 'alive'  # Default state to 'alive'

        self.fields['sex'].empty_label = None
        self.fields['sex'].required = True
        
        # Limit the father choices to male mice
        self.fields['father'].queryset = Mouse.objects.filter(sex='M')
        
        # Limit the mother choices to female mice
        self.fields['mother'].queryset = Mouse.objects.filter(sex='F')

        # Allow user to select existing strains or add a new one.
        self.fields['strain'].empty_label = None
        self.fields['strain'].queryset = Strain.objects.all()

        # If the mouse has existing earmark choices, mark the relevant checkboxes as selected
        if self.instance and self.instance.earmark:
            # Split the comma-separated string into a list of codes
            split_earmark = self.instance.earmark.split(',')
            
            # Ensure it's a list of valid choices (TL, TR, BL, BR)
            valid_choices = [choice[0] for choice in self._meta.model.CLIPPED_CHOICES]
            
            # Filter the split_earmark list to include only valid choices
            initial_choices = [choice for choice in split_earmark if choice in valid_choices]
            
            print(f"Initial earmark values (as list): {initial_choices} length: {len(initial_choices)}")
            self.fields['earmark'].initial = initial_choices

        # Filter teams based on the current user's memberships
        if user is not None:
            self.fields['team'].queryset = Team.objects.filter(teammembership__user=user)

    def clean(self):
        cleaned_data = super().clean()
        
        strain = cleaned_data.get('strain')
        new_strain = cleaned_data.get('new_strain')
        
        # If a new strain is provided, create it and assign to the Mouse instance
        if new_strain:
            strain = Strain.objects.create(name=new_strain)
            cleaned_data['strain'] = strain
            
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Convert the list of earmark choices into a comma-separated string for saving to the model
        if isinstance(instance.earmark, list):
            instance.earmark = ','.join(instance.earmark)

        if commit:
            instance.save()

        return instance

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']

class CageForm(forms.ModelForm):
    class Meta:
        model = Cage
        fields = ['cage_number', 'cage_type', 'location']

class TransferRequestForm(forms.ModelForm):
    class Meta:
        model = TransferRequest
        fields = ['mouse', 'source_cage', 'destination_cage', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter any additional comments...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Initially set the querysets for the fields
        self.fields['mouse'].queryset = Mouse.objects.exclude(state='deceased')
        self.fields['source_cage'].queryset = Cage.objects.all()
        self.fields['destination_cage'].queryset = Cage.objects.all()

        # if 'mouse' in self.data:
        #     try:
        #         mouse_id = int(self.data.get('mouse'))
        #         # Find the current cage for the selected mouse
        #         current_cage_history = CageHistory.objects.filter(
        #             mouse_id=mouse_id,
        #             end_date__isnull=True
        #         ).first()

        #         if current_cage_history:
        #             # Autofill the source cage field
        #             self.fields['source_cage'].initial = current_cage_history.cage_id
        #             # Exclude the source cage from the destination cage options
        #             self.fields['destination_cage'].queryset = Cage.objects.exclude(cage_id=current_cage_history.cage_id.cage_id)
        #     except (ValueError, TypeError):
        #         pass  # Handle the case where mouse ID is not valid
        # elif self.instance.pk:  # If editing an existing request
        #     current_cage_history = CageHistory.objects.filter(
        #         mouse_id=self.instance.mouse.id,
        #         end_date__isnull=True
        #     ).first()
        #     if current_cage_history:
        #         self.fields['source_cage'].initial = current_cage_history.cage_id
        #         self.fields['destination_cage'].queryset = Cage.objects.exclude(id=current_cage_history.cage_id.id)

    def clean(self):
        cleaned_data = super().clean()
        source_cage = cleaned_data.get("source_cage")
        destination_cage = cleaned_data.get("destination_cage")

        if source_cage and destination_cage and source_cage == destination_cage:
            self.add_error('destination_cage', "The destination cage cannot be the same as the source cage.")

        return cleaned_data

class BreedingRequestForm(forms.ModelForm):
    class Meta:
        model = BreedingRequest
        fields = ['male_mouse', 'female_mouse', 'cage', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter any additional comments...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally filter the mice and cages in the form initialization
        self.fields['male_mouse'].queryset = Mouse.objects.filter(sex='M')
        self.fields['female_mouse'].queryset = Mouse.objects.filter(sex='F')
        self.fields['cage'].queryset = Cage.objects.all()

class CullingRequestForm(forms.ModelForm):
    class Meta:
        model = CullingRequest
        fields = ['mouse', 'comments']
        widgets = {
            'comments': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter any additional comments...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optionally filter the mice in the form initialization
        self.fields['mouse'].queryset = Mouse.objects.exclude(state='deceased')