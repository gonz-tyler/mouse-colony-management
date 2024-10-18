from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from .models import Profile, Team

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=Profile.ROLE_CHOICES, required=True)
    team = forms.ModelChoiceField(queryset=Team.objects.all(), required=False)  # Assuming Team is already defined in your models

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role', 'team']

    def save(self, commit=True):
        # Save the User instance first
        user = super().save(commit=False)

        # Set additional user fields
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            # Create Profile and set team and role
            profile = Profile.objects.create(user=user)
            profile.role = self.cleaned_data['role']
            profile.team = self.cleaned_data['team']
            profile.save()

            # Automatically assign user to groups based on role
            self.assign_group_based_on_role(user, profile.role)

        return user

    def assign_group_based_on_role(self, user, role):
        """Assign the user to appropriate groups and permissions based on their role."""
        if role == 'leader':
            group = Group.objects.get(name='Leader')
        elif role == 'staff':
            group = Group.objects.get(name='Staff')
        elif role == 'new_staff':
            group = Group.objects.get(name='New Staff')
        else:
            group = None

        if group:
            user.groups.clear()  # Clear previous groups
            user.groups.add(group)

