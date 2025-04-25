from django.test import TestCase
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from django import forms
from datetime import date, datetime
from website.forms import (
    RegistrationForm, ProfileUpdateForm, AddMouseForm, TeamForm, 
    CageForm, TransferRequestForm, BreedingRequestForm, CullingRequestForm
)
from website.models import *

class RegistrationFormTest(TestCase):
    def setUp(self):
        # Common test data
        self.valid_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test.user@abdn.ac.uk',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'role': 'new_staff',
            'profile_picture': None,
            'terms_of_service': True,
            'privacy_policy': True,
        }
        
        # Create an existing user for uniqueness tests
        self.existing_user = User.objects.create_user(
            username='existing',
            email='existing.user@abdn.ac.uk',
            password='testpass123',
            first_name='Existing',
            last_name='User'
        )

    def test_form_has_correct_fields(self):
        """Test that the form contains all expected fields."""
        form = RegistrationForm()
        self.assertIn('username', form.fields)
        self.assertIn('first_name', form.fields)
        self.assertIn('last_name', form.fields)
        self.assertIn('email', form.fields)
        self.assertIn('password1', form.fields)
        self.assertIn('password2', form.fields)
        self.assertIn('role', form.fields)
        self.assertIn('profile_picture', form.fields)

    def test_form_field_requirements(self):
        """Test required fields and their attributes."""
        form = RegistrationForm()
        
        # Test required fields
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['first_name'].required)
        self.assertTrue(form.fields['last_name'].required)
        
        # Test max lengths
        self.assertEqual(form.fields['first_name'].max_length, 30)
        self.assertEqual(form.fields['last_name'].max_length, 30)

    def test_valid_form(self):
        """Test that the form is valid with correct data."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_email_validation_non_abdn_domain(self):
        """Test that non-@abdn.ac.uk emails are rejected."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'test@gmail.com'
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'Email must be an @abdn.ac.uk address.')

    def test_email_validation_duplicate(self):
        """Test that duplicate emails are rejected."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'existing.user@abdn.ac.uk'  # Already exists
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'][0], 'This email address is already in use.')

    def test_first_name_required(self):
        """Test that first_name is required."""
        invalid_data = self.valid_data.copy()
        invalid_data['first_name'] = ''
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_last_name_required(self):
        """Test that last_name is required."""
        invalid_data = self.valid_data.copy()
        invalid_data['last_name'] = ''
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_password_mismatch(self):
        """Test that password mismatch is caught."""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'DifferentPassword123!'
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_save_method(self):
        """Test that the save method correctly creates a user."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'test.user@abdn.ac.uk')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertEqual(user.username, 'testuser')
        
        # Verify the user exists in the database
        self.assertTrue(User.objects.filter(email='test.user@abdn.ac.uk').exists())

    def test_save_method_commit_false(self):
        """Test that save with commit=False doesn't save to database."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        
        user = form.save(commit=False)
        self.assertEqual(user.email, 'test.user@abdn.ac.uk')
        self.assertFalse(User.objects.filter(email='test.user@abdn.ac.uk').exists())
        
        # Now save it
        user.save()
        self.assertTrue(User.objects.filter(email='test.user@abdn.ac.uk').exists())

    def test_clean_email_valid(self):
        """Test clean_email method with valid email."""
        form = RegistrationForm(data=self.valid_data)
        form.is_valid()  # This will trigger clean_email
        self.assertEqual(form.cleaned_data['email'], 'test.user@abdn.ac.uk')

    def test_clean_email_invalid_domain(self):
        """Test clean_email with invalid domain."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'test@gmail.com'
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn("abdn.ac.uk", form.errors['email'][0])

    def test_clean_email_duplicate(self):
        """Test clean_email with duplicate email."""
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'existing.user@abdn.ac.uk'
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn("This email address is already in use.", form.errors['email'][0])

    def test_case_insensitive_email_uniqueness(self):
        """Test that email uniqueness check is case insensitive."""
        # Create user with uppercase email
        User.objects.create_user(
            username='uppercase',
            email='UPPERCASE.USER@ABDN.AC.UK',
            password='testpass123',
            first_name='Uppercase',
            last_name='User'
        )
        
        # Try to create user with same email in different case
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'uppercase.user@abdn.ac.uk'
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_role_field_required(self):
        """Test that role field is required."""
        invalid_data = self.valid_data.copy()
        invalid_data['role'] = ''
        
        form = RegistrationForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('role', form.errors)

    def test_profile_picture_not_required(self):
        """Test that profile_picture is not required."""
        valid_data = self.valid_data.copy()
        valid_data['profile_picture'] = None
        
        form = RegistrationForm(data=valid_data)
        self.assertTrue(form.is_valid())

    def test_form_meta_model(self):
        """Test that the form's Meta model is correctly set."""
        self.assertEqual(RegistrationForm.Meta.model, User)

    def test_form_meta_fields(self):
        """Test that the form's Meta fields are correctly set."""
        expected_fields = [
            'profile_picture', 'username', 'first_name', 'last_name', 
            'email', 'password1', 'password2', 'role'
        ]
        self.assertEqual(list(RegistrationForm.Meta.fields), expected_fields)

class ProfileUpdateFormTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test.user@abdn.ac.uk',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        # Create another user for uniqueness tests
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other.user@abdn.ac.uk',
            first_name='Other',
            last_name='User',
            password='testpass123'
        )
        
        # Sample image file for testing
        self.image_path = os.path.join(os.path.dirname(__file__), 'test_files', 'test.jpeg')
        with open(self.image_path, 'rb') as f:
            self.image_file = SimpleUploadedFile(
                name='test.jpeg',
                content=f.read(),
                content_type='image/jpeg'
            )

    def tearDown(self):
        # Clean up uploaded files
        if hasattr(self.user.profile_picture, 'path') and os.path.exists(self.user.profile_picture.path):
            os.remove(self.user.profile_picture.path)

    def test_form_has_correct_fields(self):
        """Test that the form contains all expected fields."""
        form = ProfileUpdateForm()
        self.assertIn('profile_picture', form.fields)
        self.assertIn('username', form.fields)
        self.assertIn('first_name', form.fields)
        self.assertIn('last_name', form.fields)

    def test_form_meta_model(self):
        """Test that the form's Meta model is correctly set."""
        self.assertEqual(ProfileUpdateForm.Meta.model, User)

    def test_form_meta_fields(self):
        """Test that the form's Meta fields are correctly set."""
        expected_fields = ['profile_picture', 'username', 'first_name', 'last_name']
        self.assertEqual(ProfileUpdateForm.Meta.fields, expected_fields)

    def test_valid_form(self):
        """Test that the form is valid with correct data."""
        form_data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        

    def test_username_uniqueness(self):
        """Test that username must be unique."""
        form_data = {
            'username': 'otheruser',  # Already taken by other_user
            'first_name': 'Test',
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'][0], 'A user with that username already exists.')

    def test_username_uniqueness_excludes_current_user(self):
        """Test that user can keep their existing username."""
        form_data = {
            'username': 'testuser',  # Current user's existing username
            'first_name': 'Test',
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_first_name_required(self):
        """Test that first_name is required."""
        form_data = {
            'username': 'testuser',
            'first_name': '',
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_last_name_required(self):
        """Test that last_name is not required."""
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': '',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())

    def test_profile_picture_not_required(self):
        """Test that profile_picture is not required."""
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_profile_picture_file_validation(self):
        """Test that invalid file types are rejected."""
        invalid_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'This is not an image',
            content_type='text/plain'
        )
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
        }
        files = {
            'profile_picture': invalid_file
        }
        form = ProfileUpdateForm(data=form_data, files=files, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('profile_picture', form.errors)

    def test_form_save_updates_user(self):
        """Test that form.save() correctly updates the user."""
        form_data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        
        # Refresh from database
        updated_user.refresh_from_db()
        
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')

    def test_form_save_without_profile_picture(self):
        """Test that form.save() works without profile picture."""
        form_data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        
        # Refresh from database
        updated_user.refresh_from_db()
        
        self.assertEqual(updated_user.username, 'updateduser')
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        self.assertFalse(updated_user.profile_picture)  # No picture was uploaded

    def test_username_max_length_validation(self):
        """Test that username respects max length validation."""
        form_data = {
            'username': 'a' * 151,  # Django's default max_length for username is 150
            'first_name': 'Test',
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_first_name_max_length_validation(self):
        """Test that first_name respects max length validation."""
        form_data = {
            'username': 'testuser',
            'first_name': 'A' * 31,  # Assuming max_length=30 from RegistrationForm
            'last_name': 'User',
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_last_name_max_length_validation(self):
        """Test that last_name respects max length validation."""
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'A' * 31,  # Assuming max_length=30 from RegistrationForm
        }
        form = ProfileUpdateForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

class AddMouseFormTest(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123'
        )
        
        # Create test strains
        self.strain1 = Strain.objects.create(name='Strain A')
        self.strain2 = Strain.objects.create(name='Strain B')
        
        # Create test teams
        self.team1 = Team.objects.create(name='Team 1')
        self.team2 = Team.objects.create(name='Team 2')
        TeamMembership.objects.create(user=self.user, team=self.team1)
        
        # Create test mice (parents)
        self.male_mouse = Mouse.objects.create(
            tube_id=1,
            sex='M',
            state='alive',
            strain=self.strain1,
            dob=date.today(),
        )
        self.female_mouse = Mouse.objects.create(
            tube_id=2,
            sex='F',
            state='alive',
            strain=self.strain1,
            dob=date.today(),
        )
        
        # Common valid form data
        self.valid_data = {
            'tube_id': 100,
            'dob': date.today(),
            'sex': 'M',
            'state': 'alive',
            'strain': self.strain1.id,
            'father': self.male_mouse.mouse_id,
            'mother': self.female_mouse.mouse_id,
            'earmark': ['TL', 'BR'],
            'genotype': 'wt',
        }

    def test_form_meta_model(self):
        """Test that the form's Meta model is correctly set."""
        self.assertEqual(AddMouseForm.Meta.model, Mouse)

    def test_form_meta_fields(self):
        """Test that the form's Meta fields are correctly set."""
        expected_fields = [
            'strain', 'tube_id', 'dob', 'sex', 'father', 'mother', 
            'earmark', 'clipped_date', 'state', 'cull_date', 'weaned', 
            'weaned_date', 'team', 'genotype'
        ]
        self.assertEqual(AddMouseForm.Meta.fields, expected_fields)

    def test_form_meta_widgets(self):
        """Test that the form's Meta widgets are correctly set."""
        self.assertIn('tube_id', AddMouseForm.Meta.widgets)
        self.assertIn('dob', AddMouseForm.Meta.widgets)
        self.assertIn('sex', AddMouseForm.Meta.widgets)
        self.assertIn('clipped_date', AddMouseForm.Meta.widgets)
        self.assertIn('cull_date', AddMouseForm.Meta.widgets)
        self.assertIn('weaned_date', AddMouseForm.Meta.widgets)

    def test_form_field_types(self):
        """Test that form fields are of correct types."""
        form = AddMouseForm(user=self.user)
        self.assertEqual(form.fields['team'].__class__.__name__, 'ModelChoiceField')
        self.assertEqual(form.fields['earmark'].__class__.__name__, 'MultipleChoiceField')
        self.assertEqual(form.fields['strain'].__class__.__name__, 'ModelChoiceField')
        self.assertEqual(form.fields['new_strain'].__class__.__name__, 'CharField')
        self.assertEqual(form.fields['genotype'].__class__.__name__, 'ChoiceField')

    def test_form_field_requirements(self):
        """Test required/optional fields."""
        form = AddMouseForm(user=self.user)
        self.assertTrue(form.fields['sex'].required)
        self.assertFalse(form.fields['team'].required)
        self.assertFalse(form.fields['earmark'].required)
        self.assertFalse(form.fields['strain'].required)
        self.assertFalse(form.fields['new_strain'].required)
        self.assertFalse(form.fields['genotype'].required)

    def test_form_initial_values(self):
        """Test form initial values."""
        form = AddMouseForm(user=self.user)
        self.assertEqual(form.fields['state'].initial, 'alive')
        self.assertIsNone(form.fields['sex'].empty_label)

    def test_valid_form(self):
        """Test that the form is valid with correct data."""
        form = AddMouseForm(data=self.valid_data, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_team_queryset_filtering(self):
        """Test that team queryset is filtered by user membership."""
        form = AddMouseForm(user=self.user)
        self.assertEqual(form.fields['team'].queryset.count(), 1)
        self.assertEqual(form.fields['team'].queryset.first(), self.team1)
        
        # Test with a different user
        user2 = User.objects.create_user(username='user2', email='user2@abdn.ac.uk', password='testpass123')
        form = AddMouseForm(user=user2)
        self.assertEqual(form.fields['team'].queryset.count(), 0)

    def test_father_queryset_filtering(self):
        """Test that father queryset is filtered to male mice."""
        form = AddMouseForm(user=self.user)
        self.assertTrue(all(mouse.sex == 'M' for mouse in form.fields['father'].queryset))

    def test_mother_queryset_filtering(self):
        """Test that mother queryset is filtered to female mice."""
        form = AddMouseForm(user=self.user)
        self.assertTrue(all(mouse.sex == 'F' for mouse in form.fields['mother'].queryset))

    def test_earmark_validation(self):
        """Test earmark field validation."""
        # Valid earmark choices
        valid_data = self.valid_data.copy()
        valid_data['earmark'] = ['TL', 'BR']
        form = AddMouseForm(data=valid_data, user=self.user)
        self.assertTrue(form.is_valid())
        
        # Invalid earmark choices
        invalid_data = self.valid_data.copy()
        invalid_data['earmark'] = ['XX', 'YY']  # Invalid choices
        form = AddMouseForm(data=invalid_data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('earmark', form.errors)

    def test_clean_earmark_method(self):
        """Test the clean_earmark method."""
        form = AddMouseForm(data={'earmark': ['TL', 'BR']}, user=self.user)
        form.is_valid()  # Trigger cleaning
        self.assertEqual(form.cleaned_data['earmark'], ['TL', 'BR'])

    def test_clean_method_with_new_strain(self):
        """Test the clean method with new strain creation."""
        data = self.valid_data.copy()
        data.pop('strain')  # Remove strain selection
        data['new_strain'] = 'New Strain C'
        
        form = AddMouseForm(data=data, user=self.user)
        form.is_valid()  # Trigger validation
        
        
        # Verify new strain was created
        self.assertEqual(Strain.objects.filter(name='New Strain C').count(), 0)  # Not created yet
        form.save()
        self.assertTrue(form.is_valid())
        form.clean()
        self.assertEqual(Strain.objects.filter(name='New Strain C').count(), 1)  # Created during save

    def test_clean_method_with_existing_strain(self):
        """Test the clean method with existing strain."""
        data = self.valid_data.copy()
        data['new_strain'] = ''  # Empty new strain
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        cleaned_data = form.clean()
        self.assertEqual(cleaned_data['strain'], self.strain1)
        self.assertEqual(Strain.objects.count(), 2)  # No new strain created

    def test_save_method_with_earmark(self):
        """Test the save method with earmark data."""
        data = self.valid_data.copy()
        data['earmark'] = ['TL', 'BR']
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        mouse = form.save()
        
        # Verify earmark was saved correctly
        mouse.refresh_from_db()
        self.assertEqual(mouse.earmark, 'TL,BR')

    def test_save_method_without_earmark(self):
        """Test the save method without earmark data."""
        data = self.valid_data.copy()
        data['earmark'] = None
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        mouse = form.save()
        
        # Verify earmark is empty
        mouse.refresh_from_db()
        self.assertEqual(mouse.earmark, '')

    def test_tube_id_required(self):
        """Test that tube_id is required."""
        data = self.valid_data.copy()
        data['tube_id'] = ''
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('tube_id', form.errors)

    def test_tube_id_unique(self):
        """Test that tube_id must be unique."""
        Mouse.objects.create(strain=self.strain1, tube_id=100, sex='M', state='alive', dob=date.today())
        data = self.valid_data.copy()  # Uses tube_id=100
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Mouse with this Strain and Tube id already exists.', form.errors['__all__'])

    def test_dob_required(self):
        """Test that dob is required."""
        data = self.valid_data.copy()
        data['dob'] = ''
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('dob', form.errors)

    def test_sex_required(self):
        """Test that sex is required."""
        data = self.valid_data.copy()
        data['sex'] = ''
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('sex', form.errors)

    def test_state_default_value(self):
        """Test that state defaults to 'alive'."""
        data = self.valid_data.copy()
        data.pop('state', None)  # Remove state
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['state'], 'alive')

    def test_date_field_validation(self):
        """Test validation for date fields."""
        # Test invalid date format for dob
        data = self.valid_data.copy()
        data['dob'] = 'invalid-date'
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('dob', form.errors)

        # Test invalid date format for clipped_date
        data = self.valid_data.copy()
        data['clipped_date'] = 'invalid-date'
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('clipped_date', form.errors)

    def test_initial_earmark_for_existing_instance(self):
        """Test that earmark initial values are set correctly for existing instances."""
        # Create a mouse with earmark
        mouse = Mouse.objects.create(
            strain=self.strain1,
            tube_id=101,
            sex='M',
            state='alive',
            earmark='TL,BR',
            dob=date.today(),
        )
        
        form = AddMouseForm(instance=mouse, user=self.user)
        self.assertEqual(form.fields['earmark'].initial, ['TL', 'BR'])

    def test_initial_earmark_for_new_instance(self):
        """Test that earmark initial values are empty for new instances."""
        form = AddMouseForm(user=self.user)
        self.assertEqual(form.fields['earmark'].initial, None)

    def test_genotype_choices(self):
        """Test that genotype choices match the model's choices."""
        form = AddMouseForm(user=self.user)
        self.assertEqual(form.fields['genotype'].choices, Mouse.GENOTYPE_CHOICES)

    def test_weaned_date_required_when_weaned_true(self):
        """Test that weaned_date is required when weaned is True."""
        data = self.valid_data.copy()
        data['weaned'] = True
        data['weaned_date'] = ''
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('weaned_date', form.errors)

    def test_weaned_date_not_required_when_weaned_false(self):
        """Test that weaned_date is not required when weaned is False."""
        data = self.valid_data.copy()
        data['weaned'] = False
        data['weaned_date'] = ''
        
        form = AddMouseForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())

class TeamFormTest(TestCase):
    def test_form_meta_model(self):
        """Test that the form uses the correct model."""
        self.assertEqual(TeamForm._meta.model, Team)

    def test_form_meta_fields(self):
        """Test that the form includes the correct fields."""
        self.assertEqual(TeamForm._meta.fields, ['name'])

    def test_valid_data(self):
        """Form should be valid with correct data."""
        form = TeamForm(data={'name': 'Team Alpha'})
        self.assertTrue(form.is_valid())

    def test_blank_name(self):
        """Form should be invalid if name is blank."""
        form = TeamForm(data={'name': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_missing_name_field(self):
        """Form should be invalid if name field is missing."""
        form = TeamForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_form_save(self):
        """Form should save and create a Team instance."""
        form = TeamForm(data={'name': 'Team Omega'})
        self.assertTrue(form.is_valid())
        team = form.save()
        self.assertIsInstance(team, Team)
        self.assertEqual(team.name, 'Team Omega')

    def test_name_field_max_length(self):
        """Ensure form respects max_length defined on model."""
        max_length = Team._meta.get_field('name').max_length
        form = TeamForm(data={'name': 'a' * (max_length + 1)})
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

    def test_name_with_whitespace(self):
        """Test form handling name with leading/trailing whitespace."""
        form = TeamForm(data={'name': '  Team Zeta  '})
        self.assertTrue(form.is_valid())
        team = form.save()
        self.assertEqual(team.name, 'Team Zeta')

    def test_name_with_special_characters(self):
        """Form should allow special characters unless model restricts them."""
        form = TeamForm(data={'name': '@Team#1!'})
        self.assertTrue(form.is_valid())

    def test_duplicate_team_name(self):
        """Test for duplicate names if model enforces uniqueness."""
        Team.objects.create(name='Team Unique')
        form = TeamForm(data={'name': 'Team Unique'})
        if Team._meta.get_field('name').unique:
            self.assertFalse(form.is_valid())
            self.assertIn('name', form.errors)
        else:
            self.assertTrue(form.is_valid())

class CageFormTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'cage_number': 'C123',
            'cage_type': 'Standard',
            'location': 'North Wing',
        }

    def test_form_meta_model(self):
        """Test that the form uses the correct model."""
        self.assertEqual(CageForm._meta.model, Cage)

    def test_form_meta_fields(self):
        """Test that the form includes the correct fields."""
        self.assertEqual(CageForm._meta.fields, ['cage_number', 'cage_type', 'location'])

    def test_valid_data(self):
        """Form should be valid with correct data."""
        form = CageForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_blank_fields(self):
        """Form should be invalid if required fields are blank."""
        for field in self.valid_data:
            data = self.valid_data.copy()
            data[field] = ''
            form = CageForm(data=data)
            self.assertFalse(form.is_valid(), msg=f"Form should be invalid when {field} is blank")
            self.assertIn(field, form.errors)

    def test_missing_fields(self):
        """Form should be invalid if any field is missing."""
        for field in self.valid_data:
            data = self.valid_data.copy()
            del data[field]
            form = CageForm(data=data)
            self.assertFalse(form.is_valid(), msg=f"Form should be invalid when {field} is missing")
            self.assertIn(field, form.errors)

    def test_save_form(self):
        """Form should save and create a Cage instance."""
        form = CageForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        cage = form.save()
        self.assertIsInstance(cage, Cage)
        self.assertEqual(cage.cage_number, self.valid_data['cage_number'])
        self.assertEqual(cage.cage_type, self.valid_data['cage_type'])
        self.assertEqual(cage.location, self.valid_data['location'])

    def test_max_length_constraints(self):
        """Test max_length constraints based on model field settings."""
        for field_name in ['cage_number', 'cage_type', 'location']:
            field = Cage._meta.get_field(field_name)
            if hasattr(field, 'max_length') and field.max_length:
                data = self.valid_data.copy()
                data[field_name] = 'x' * (field.max_length + 1)
                form = CageForm(data=data)
                self.assertFalse(form.is_valid(), msg=f"{field_name} should respect max_length")
                self.assertIn(field_name, form.errors)

    def test_whitespace_handling(self):
        """Test handling of leading/trailing whitespaces in fields."""
        form = CageForm(data={'cage_number': '  C123  ', 'cage_type': '  Standard  ', 'location': '  North Wing  '})
        self.assertTrue(form.is_valid())
        cage = form.save()
        self.assertEqual(cage.cage_number, 'C123')

    def test_special_characters_allowed(self):
        """Test if fields accept special characters unless explicitly restricted."""
        special_data = {
            'cage_number': 'C@#123!',
            'cage_type': 'Type*&^%',
            'location': 'Loc()!~',
        }
        form = CageForm(data=special_data)
        self.assertTrue(form.is_valid())

    def test_duplicate_cage_number(self):
        """Test duplicate cage_number if model enforces uniqueness."""
        Cage.objects.create(**self.valid_data)
        form = CageForm(data=self.valid_data)
        if Cage._meta.get_field('cage_number').unique:
            self.assertFalse(form.is_valid())
            self.assertIn('cage_number', form.errors)
        else:
            self.assertTrue(form.is_valid())

class TransferRequestFormTest(TestCase):
    def setUp(self):
        strain1 = Strain.objects.create(name="Strain A")
        self.mouse_alive = Mouse.objects.create(strain=strain1, state="alive", tube_id='100', dob=date.today())
        self.mouse_deceased = Mouse.objects.create(strain=strain1, state="deceased", tube_id='101', dob=date.today())

        self.cage1 = Cage.objects.create(cage_number="C1", cage_type="Standard", location="North")
        self.cage2 = Cage.objects.create(cage_number="C2", cage_type="Standard", location="South")

        self.valid_data = {
            'mouse': self.mouse_alive.mouse_id,
            'source_cage': self.cage1.cage_id,
            'destination_cage': self.cage2.cage_id,
            'comments': 'Transfer request test.'
        }

    def test_meta_fields(self):
        """Check that the form includes the correct fields."""
        self.assertEqual(TransferRequestForm._meta.fields, ['mouse', 'source_cage', 'destination_cage', 'comments'])

    def test_comments_widget(self):
        """Check if comments field uses custom Textarea widget."""
        form = TransferRequestForm()
        self.assertIsInstance(form.fields['comments'].widget, forms.Textarea)
        self.assertEqual(form.fields['comments'].widget.attrs.get('rows'), 4)

    def test_mouse_queryset_excludes_deceased(self):
        """Mouse queryset should exclude deceased mice."""
        form = TransferRequestForm()
        self.assertNotIn(self.mouse_deceased, form.fields['mouse'].queryset)
        self.assertIn(self.mouse_alive, form.fields['mouse'].queryset)

    def test_source_and_destination_queryset(self):
        """Source and destination cages should include all cages by default."""
        form = TransferRequestForm()
        actual = list(form.fields['source_cage'].queryset.order_by('cage_id'))
        expected = list(Cage.objects.order_by('cage_id'))
        self.assertEqual(actual, expected)

    def test_valid_form_submission(self):
        """Form should be valid with correct data."""
        form = TransferRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_invalid_when_cages_are_same(self):
        """Form should be invalid if source and destination cages are the same."""
        data = self.valid_data.copy()
        data['destination_cage'] = self.cage1.cage_id  # same as source
        form = TransferRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('destination_cage', form.errors)
        self.assertEqual(
            form.errors['destination_cage'][0],
            "The destination cage cannot be the same as the source cage."
        )

    def test_missing_required_fields(self):
        """Each required field missing should cause form to be invalid."""
        for field in ['mouse', 'source_cage', 'destination_cage']:
            data = self.valid_data.copy()
            data.pop(field)
            form = TransferRequestForm(data=data)
            self.assertFalse(form.is_valid(), msg=f"{field} missing should make form invalid.")
            self.assertIn(field, form.errors)

    def test_optional_comments_field(self):
        """Comments should be optional."""
        data = self.valid_data.copy()
        data.pop('comments')
        form = TransferRequestForm(data=data)
        self.assertTrue(form.is_valid(), msg="Form should be valid even without comments.")

    def test_save_form(self):
        """Test saving a valid form."""
        form = TransferRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.mouse, self.mouse_alive)
        self.assertEqual(instance.source_cage, self.cage1)
        self.assertEqual(instance.destination_cage, self.cage2)
        self.assertEqual(instance.comments, self.valid_data['comments'])

class BreedingRequestFormTest(TestCase):
    def setUp(self):
        strain1 = Strain.objects.create(name="Strain A")
        self.male_mouse = Mouse.objects.create(strain=strain1, sex='M', state="alive", tube_id='100', dob=date.today())
        self.female_mouse = Mouse.objects.create(strain=strain1, sex='F', state="alive", tube_id='101', dob=date.today())
        self.wrong_sex_mouse = Mouse.objects.create(strain=strain1, sex='X', state="alive", tube_id='102', dob=date.today())

        self.cage = Cage.objects.create(cage_number="C1", cage_type="Breeding", location="West Wing")

        self.valid_data = {
            'male_mouse': self.male_mouse.mouse_id,
            'female_mouse': self.female_mouse.mouse_id,
            'cage': self.cage.cage_id,
            'comments': 'Pairing Alpha and Beta for breeding.'
        }

    def test_meta_fields(self):
        """Check that the form uses the correct model and fields."""
        self.assertEqual(BreedingRequestForm._meta.model, BreedingRequest)
        self.assertEqual(
            BreedingRequestForm._meta.fields,
            ['male_mouse', 'female_mouse', 'cage', 'comments']
        )

    def test_comments_widget(self):
        """Ensure comments uses a Textarea with correct attributes."""
        form = BreedingRequestForm()
        widget = form.fields['comments'].widget
        self.assertIsInstance(widget, forms.Textarea)
        self.assertEqual(widget.attrs.get('rows'), 4)
        self.assertIn('placeholder', widget.attrs)

    def test_male_mouse_queryset(self):
        """Form should include only male mice in the male_mouse field."""
        form = BreedingRequestForm()
        self.assertIn(self.male_mouse, form.fields['male_mouse'].queryset)
        self.assertNotIn(self.female_mouse, form.fields['male_mouse'].queryset)
        self.assertNotIn(self.wrong_sex_mouse, form.fields['male_mouse'].queryset)

    def test_female_mouse_queryset(self):
        """Form should include only female mice in the female_mouse field."""
        form = BreedingRequestForm()
        self.assertIn(self.female_mouse, form.fields['female_mouse'].queryset)
        self.assertNotIn(self.male_mouse, form.fields['female_mouse'].queryset)
        self.assertNotIn(self.wrong_sex_mouse, form.fields['female_mouse'].queryset)

    def test_cage_queryset(self):
        """All cages should be available for selection."""
        form = BreedingRequestForm()
        self.assertIn(self.cage, form.fields['cage'].queryset)

    def test_valid_form_submission(self):
        """Form should be valid with correct data."""
        form = BreedingRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_missing_required_fields(self):
        """Each required field missing should make the form invalid."""
        for field in ['male_mouse', 'female_mouse', 'cage']:
            data = self.valid_data.copy()
            data.pop(field)
            form = BreedingRequestForm(data=data)
            self.assertFalse(form.is_valid(), msg=f"{field} missing should make form invalid.")
            self.assertIn(field, form.errors)

    def test_optional_comments_field(self):
        """Form should be valid without comments."""
        data = self.valid_data.copy()
        data.pop('comments')
        form = BreedingRequestForm(data=data)
        self.assertTrue(form.is_valid())

    def test_save_form(self):
        """Test saving a valid form creates a BreedingRequest."""
        form = BreedingRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        request = form.save()
        self.assertEqual(request.male_mouse, self.male_mouse)
        self.assertEqual(request.female_mouse, self.female_mouse)
        self.assertEqual(request.cage, self.cage)
        self.assertEqual(request.comments, self.valid_data['comments'])

class CullingRequestFormTest(TestCase):
    def setUp(self):
        """Setup test mice."""
        strain1 = Strain.objects.create(name="Strain A")
        self.alive_mouse = Mouse.objects.create(strain=strain1, sex='M', state="alive", tube_id='100', dob=date.today())
        self.deceased_mouse = Mouse.objects.create(strain=strain1, sex='M', state="deceased", tube_id='101', dob=date.today())

        self.valid_data = {
            'mouse': self.alive_mouse.mouse_id,
            'comments': 'This is a culling request for testing.'
        }

    def test_meta_fields(self):
        """Tests form Meta model and fields."""
        self.assertEqual(CullingRequestForm._meta.model, CullingRequest)
        self.assertEqual(CullingRequestForm._meta.fields, ['mouse', 'comments'])

    def test_comments_widget(self):
        """Tests custom Textarea widget for comments field."""
        form = CullingRequestForm()
        widget = form.fields['comments'].widget
        self.assertIsInstance(widget, forms.Textarea)
        self.assertEqual(widget.attrs.get('rows'), 4)
        self.assertEqual(widget.attrs.get('placeholder'), 'Enter any additional comments...')

    def test_mouse_queryset_excludes_deceased(self):
        """Tests mouse queryset excludes deceased mice."""
        form = CullingRequestForm()
        self.assertIn(self.alive_mouse, form.fields['mouse'].queryset)
        self.assertNotIn(self.deceased_mouse, form.fields['mouse'].queryset)

    def test_valid_form_submission(self):
        """Tests form is valid with correct data."""
        form = CullingRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_missing_mouse_field(self):
        """Tests form invalid if mouse is missing."""
        data = self.valid_data.copy()
        data.pop('mouse')
        form = CullingRequestForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('mouse', form.errors)

    def test_optional_comments_field(self):
        """Tests form valid when comments field is omitted."""
        data = self.valid_data.copy()
        data.pop('comments')
        form = CullingRequestForm(data=data)
        self.assertTrue(form.is_valid())

    def test_save_form(self):
        """Tests saving a valid form creates a CullingRequest."""
        form = CullingRequestForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        instance = form.save()
        self.assertEqual(instance.mouse, self.alive_mouse)
        self.assertEqual(instance.comments, self.valid_data['comments'])