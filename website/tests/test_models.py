from django.test import TestCase
from website.models import *
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime as dt
from datetime import date
from unittest.mock import patch

class CageModelTest(TestCase):
    def setUp(self):
        """Sets up a test cage instance."""
        self.cage = Cage.objects.create(
            cage_number="C-001",
            cage_type="Standard",
            location="West Wing"
        )

    def test_cage_creation(self):
        """Tests cage instance is created correctly."""
        self.assertEqual(self.cage.cage_number, "C-001")
        self.assertEqual(self.cage.cage_type, "Standard")
        self.assertEqual(self.cage.location, "West Wing")

    def test_cage_str_representation(self):
        """Tests __str__ returns cage_number."""
        self.assertEqual(str(self.cage), "C-001")

    def test_cage_number_uniqueness(self):
        """Tests cage_number must be unique."""
        with self.assertRaises(Exception):
            Cage.objects.create(
                cage_number="C-001",  # duplicate
                cage_type="Duplicate",
                location="East Wing"
            )

class CageHistoryModelTest(TestCase):
    def setUp(self):
        """Sets up test cage and mouse instances."""
        self.cage = Cage.objects.create(
            cage_number="C-002",
            cage_type="Quarantine",
            location="East Wing"
        )
        self.strain = Strain.objects.create(name='Strain A')
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            dob=timezone.now().date(),
            sex='M',
            state='alive'
        )
        self.start_date = timezone.now()
        self.end_date = self.start_date + timezone.timedelta(days=5)

    def test_cage_history_creation(self):
        """Tests valid CageHistory instance is saved correctly."""
        history = CageHistory.objects.create(
            cage_id=self.cage,
            mouse_id=self.mouse,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.assertEqual(history.cage_id, self.cage)
        self.assertEqual(history.mouse_id, self.mouse)
        self.assertEqual(history.start_date, self.start_date)
        self.assertEqual(history.end_date, self.end_date)

    def test_end_date_optional(self):
        """Tests CageHistory can be created without end_date."""
        history = CageHistory.objects.create(
            cage_id=self.cage,
            mouse_id=self.mouse,
            start_date=self.start_date,
        )
        self.assertIsNone(history.end_date)

    def test_end_date_before_start_date_validation(self):
        """Tests validation error is raised when end_date is before start_date."""
        with self.assertRaises(ValidationError):
            CageHistory.objects.create(
                cage_id=self.cage,
                mouse_id=self.mouse,
                start_date=self.start_date,
                end_date=self.start_date - timezone.timedelta(days=1)
            )

    def test_save_triggers_clean_validation(self):
        """Tests that save calls clean and triggers validation logic."""
        history = CageHistory(
            cage_id=self.cage,
            mouse_id=self.mouse,
            start_date=self.start_date,
            end_date=self.start_date - timezone.timedelta(days=2)
        )
        with self.assertRaises(ValidationError):
            history.save()

class UserModelTest(TestCase):
    def setUp(self):
        """Sets up baseline user data."""
        self.valid_email = "user@abdn.ac.uk"
        self.invalid_email = "user@gmail.com"

    def test_default_role(self):
        """Tests default role is 'new_staff'."""
        user = User.objects.create_user(username="default_role_user", email=self.valid_email, password="pass123")
        self.assertEqual(user.role, 'new_staff')

    def test_email_uniqueness(self):
        """Tests email must be unique."""
        User.objects.create_user(username="first", email=self.valid_email, password="pass123")
        with self.assertRaises(Exception):
            User.objects.create_user(username="second", email=self.valid_email, password="pass456")

    def test_valid_email_passes_validation(self):
        """Tests that valid @abdn.ac.uk emails pass validation."""
        user = User(username="validuser", email=self.valid_email, password="pass123")
        try:
            user.full_clean()
        except ValidationError:
            self.fail("ValidationError raised unexpectedly!")

    def test_invalid_email_raises_validation(self):
        """Tests that non-@abdn.ac.uk emails raise ValidationError."""
        user = User(username="invaliduser", email=self.invalid_email)
        with self.assertRaises(ValidationError) as cm:
            user.full_clean()
        self.assertIn("Email must be an @abdn.ac.uk address.", str(cm.exception))

    def test_str_method(self):
        """Tests __str__ returns username."""
        user = User.objects.create_user(username="sampleuser", email=self.valid_email, password="pass123")
        self.assertEqual(str(user), "sampleuser")

class TeamModelTest(TestCase):
    def setUp(self):
        """Sets up a test team instance."""
        self.team = Team.objects.create(name="Genetics Research")

    def test_team_creation(self):
        """Tests team instance is created with correct values."""
        self.assertEqual(self.team.name, "Genetics Research")
        self.assertIsNotNone(self.team.created_at)

    def test_team_str_representation(self):
        """Tests __str__ returns the team name."""
        self.assertEqual(str(self.team), "Genetics Research")

    def test_team_name_uniqueness(self):
        """Tests team name must be unique."""
        with self.assertRaises(Exception):
            Team.objects.create(name="Genetics Research")

class TeamMembershipModelTest(TestCase):
    def setUp(self):
        """Sets up user and team instances for membership testing."""
        self.user = User.objects.create_user(username="john", email="john@abdn.ac.uk", password="pass123")
        self.team = Team.objects.create(name="Behavioral Research")
        self.membership = TeamMembership.objects.create(user=self.user, team=self.team)

    def test_membership_creation(self):
        """Tests TeamMembership instance is created correctly."""
        self.assertEqual(self.membership.user, self.user)
        self.assertEqual(self.membership.team, self.team)

    def test_membership_str_representation(self):
        """Tests __str__ method returns expected string."""
        expected_str = f"{self.user.username} - {self.team.name} ({self.user.role})"
        self.assertEqual(str(self.membership), expected_str)

    def test_unique_membership_constraint(self):
        """Tests that user cannot be added to the same team twice."""
        with self.assertRaises(Exception):
            TeamMembership.objects.create(user=self.user, team=self.team)

class MouseModelTest(TestCase):
    def setUp(self):
        """Sets up test data for Mouse model."""
        self.strain = Strain.objects.create(name="C57BL/6")
        self.user = User.objects.create_user(username="testuser", email="test@abdn.ac.uk", password="pass123")
        self.team = Team.objects.create(name="Neuro Research")
        TeamMembership.objects.create(user=self.user, team=self.team)

        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            dob=date(2023, 1, 1),
            sex='M',
            genotype='ht',
            earmark=["TL", "BR"]
        )

    def test_mouse_str(self):
        """Tests __str__ returns expected format."""
        self.assertIn("Mouse", str(self.mouse))
        self.assertIn("Tube", str(self.mouse))

    def test_unique_tube_id_per_strain(self):
        """Tests that tube_id must be unique per strain."""
        with self.assertRaises(Exception):
            Mouse.objects.create(strain=self.strain, tube_id=1, dob=date(2023, 2, 2), sex='F')

    def test_get_earmark_choices(self):
        """Tests get_earmark_choices returns earmark list."""
        self.assertEqual(self.mouse.get_earmark_choices(), ["TL", "BR"])

    def test_set_earmark_choices_valid(self):
        """Tests setting earmark list via method."""
        self.mouse.set_earmark_choices(["BL"])
        self.assertEqual(self.mouse.earmark, ["BL"])

    def test_set_earmark_choices_invalid(self):
        """Tests ValueError raised when passing non-list to set_earmark_choices."""
        with self.assertRaises(ValueError):
            self.mouse.set_earmark_choices("BL")

    def test_get_earmark_display(self):
        """Tests earmark display string output."""
        self.assertEqual(self.mouse.get_earmark_display(), "Top LeftBottom Right")

    def test_get_genotype_display(self):
        """Tests genotype display label is returned correctly."""
        self.assertEqual(self.mouse.get_genotype_display(), "Heterozygous")

    def test_get_parents_and_ancestors(self):
        """Tests parent and ancestor retrieval logic."""
        mother = Mouse.objects.create(strain=self.strain, tube_id=2, dob=date(2022, 5, 1), sex='F')
        father = Mouse.objects.create(strain=self.strain, tube_id=3, dob=date(2022, 5, 1), sex='M')
        child = Mouse.objects.create(strain=self.strain, tube_id=4, dob=date(2024, 1, 1), sex='M', mother=mother, father=father)

        self.assertIn(mother, child.get_parents())
        self.assertIn(father, child.get_ancestors())
        self.assertIn(child, mother.get_descendants())

    def test_is_kept_by_user(self):
        """Tests mouse is linked to user via MouseKeeper."""
        MouseKeeper.objects.create(mouse=self.mouse, user=self.user, start_date=timezone.now())
        self.assertTrue(self.mouse.is_kept_by_user(self.user))

    def test_is_kept_by_team(self):
        """Tests mouse is linked to team via MouseKeeper."""
        MouseKeeper.objects.create(mouse=self.mouse, team=self.team, start_date=timezone.now())
        self.assertTrue(self.mouse.is_kept_by_team(self.team))

    def test_mice_managed_by_user_combines_direct_and_team(self):
        """Tests that mice_managed_by_user returns all relevant mice without duplicates."""
        MouseKeeper.objects.create(mouse=self.mouse, user=self.user, start_date=timezone.now())
        MouseKeeper.objects.create(mouse=self.mouse, team=self.team, start_date=timezone.now())
        mice = Mouse.mice_managed_by_user(self.user)
        self.assertIn(self.mouse, mice)
        self.assertEqual(mice.count(), 1)

class MouseKeeperModelTest(TestCase):
    def setUp(self):
        """Sets up base data for MouseKeeper model tests."""
        self.strain = Strain.objects.create(name="Test Strain")
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            dob=timezone.now().date(),
            sex='M'
        )
        self.user = User.objects.create_user(username="keeperuser", email="keeper@abdn.ac.uk", password="pass123")
        self.team = Team.objects.create(name="Caretakers")

    def test_valid_user_mousekeeper(self):
        """Tests valid MouseKeeper with user only."""
        keeper = MouseKeeper(
            mouse=self.mouse,
            user=self.user,
            start_date=timezone.now()
        )
        keeper.full_clean()  # Should not raise
        keeper.save()
        self.assertEqual(str(keeper), f"Mouse {self.mouse.mouse_id} - Keeper {self.user}")

    def test_valid_team_mousekeeper(self):
        """Tests valid MouseKeeper with team only."""
        keeper = MouseKeeper(
            mouse=self.mouse,
            team=self.team,
            start_date=timezone.now()
        )
        keeper.full_clean()
        keeper.save()
        self.assertEqual(str(keeper), f"Mouse {self.mouse.mouse_id} - Keeper {self.team}")

    def test_invalid_mousekeeper_with_both_user_and_team(self):
        """Tests MouseKeeper cannot have both user and team."""
        keeper = MouseKeeper(
            mouse=self.mouse,
            user=self.user,
            team=self.team,
            start_date=timezone.now()
        )
        with self.assertRaises(ValidationError) as context:
            keeper.full_clean()
        self.assertIn("only one of user or team", str(context.exception))

    def test_invalid_mousekeeper_with_neither_user_nor_team(self):
        """Tests MouseKeeper must have at least a user or a team."""
        keeper = MouseKeeper(
            mouse=self.mouse,
            start_date=timezone.now()
        )
        with self.assertRaises(ValidationError) as context:
            keeper.full_clean()
        self.assertIn("at least one keeper", str(context.exception))

    # def test_unique_constraint_user_and_team(self):
    #     """Tests unique_together constraint on mouse, user, team."""
    #     MouseKeeper.objects.create(mouse=self.mouse, user=self.user, start_date=timezone.now())
    #     duplicate = MouseKeeper(mouse=self.mouse, user=self.user, start_date=timezone.now())
    #     with self.assertRaises(Exception):
    #         duplicate.save()

class BreedingRequestModelTest(TestCase):
    def setUp(self):
        """Sets up test data for BreedingRequest."""
        self.strain = Strain.objects.create(name="C57BL/6")
        self.user = User.objects.create_user(username="testuser", email="test@abdn.ac.uk", password="testpass")
        self.male_mouse = Mouse.objects.create(
            strain=self.strain, tube_id=101, dob="2023-01-01", sex='M', state='alive', genotype='wt'
        )
        self.female_mouse = Mouse.objects.create(
            strain=self.strain, tube_id=102, dob="2023-01-01", sex='F', state='alive', genotype='wt'
        )
        self.cage = Cage.objects.create(cage_number="C123", cage_type="Standard", location="A1")

    def create_request(self, **kwargs):
        """Helper to create a BreedingRequest."""
        return BreedingRequest.objects.create(
            male_mouse=self.male_mouse,
            female_mouse=self.female_mouse,
            cage=self.cage,
            requester=self.user,
            **kwargs
        )

    def test_valid_breeding_request(self):
        """Tests valid BreedingRequest creation."""
        request = self.create_request()
        self.assertEqual(request.status, "pending")
        self.assertEqual(request.male_mouse.sex, "M")
        self.assertEqual(request.female_mouse.sex, "F")
        self.assertEqual(request.cage, self.cage)

    def test_invalid_breeding_mouse_combination(self):
        """Tests that invalid mouse sexes raise ValidationError."""
        self.male_mouse.sex = 'F'
        self.male_mouse.save()
        request = self.create_request()
        with self.assertRaises(ValidationError):
            request.clean()

    def test_missing_cage_raises_validation(self):
        """Tests that missing cage raises ValidationError."""
        request = BreedingRequest(
            male_mouse=self.male_mouse,
            female_mouse=self.female_mouse,
            requester=self.user
        )
        with self.assertRaises(ValidationError):
            request.clean()

    def test_approve_method(self):
        """Tests approve method changes status and creates a Breed."""
        request = self.create_request()
        request.approve(approver=self.user)

        request.refresh_from_db()
        self.assertEqual(request.status, 'approved')
        self.assertEqual(request.male_mouse.state, 'breeding')
        self.assertEqual(request.female_mouse.state, 'breeding')
        self.assertTrue(Breed.objects.filter(male=self.male_mouse, female=self.female_mouse).exists())

    def test_complete_method(self):
        """Tests complete method sets status to 'completed'."""
        request = self.create_request()
        request.complete()
        self.assertEqual(request.status, 'completed')

    def test_reject_method(self):
        """Tests reject method sets status to 'rejected'."""
        request = self.create_request()
        request.reject()
        self.assertEqual(request.status, 'rejected')

class CullingRequestModelTest(TestCase):
    def setUp(self):
        """Sets up test data for CullingRequest."""
        self.strain = Strain.objects.create(name="C57BL/6")
        self.user = User.objects.create_user(username="culler", email="culler@abdn.ac.uk", password="pass1234")
        self.mouse = Mouse.objects.create(
            strain=self.strain, tube_id=103, dob="2023-01-01", sex='F', state='alive', genotype='wt'
        )

    def create_request(self, **kwargs):
        """Helper to create a CullingRequest."""
        return CullingRequest.objects.create(mouse=self.mouse, requester=self.user, **kwargs)

    def test_valid_culling_request(self):
        """Tests valid CullingRequest creation."""
        request = self.create_request()
        self.assertEqual(request.status, "pending")
        self.assertEqual(request.mouse, self.mouse)
        self.assertEqual(request.requester, self.user)

    def test_approve_method(self):
        """Tests approve method updates status and sets approval date."""
        request = self.create_request()
        request.approve(approver=self.user)
        request.refresh_from_db()
        self.assertEqual(request.status, "approved")
        self.assertIsNotNone(request.approval_date)

    def test_complete_method(self):
        """Tests complete method marks request and mouse as completed/deceased."""
        request = self.create_request()
        request.complete()
        request.refresh_from_db()
        self.mouse.refresh_from_db()

        self.assertEqual(request.status, "completed")
        self.assertEqual(self.mouse.state, "deceased")
        self.assertIsNotNone(self.mouse.cull_date)

    def test_reject_method(self):
        """Tests reject method updates status to 'rejected'."""
        request = self.create_request()
        request.reject()
        self.assertEqual(request.status, "rejected")

class TransferRequestModelTest(TestCase):
    def setUp(self):
        """Sets up test data for TransferRequest."""
        self.strain = Strain.objects.create(name="C57BL/6")
        self.user = User.objects.create_user(username="transfer_requester", email="requester@abdn.ac.uk", password="pass1234")
        self.mouse = Mouse.objects.create(
            strain=self.strain, tube_id=104, dob="2023-01-01", sex='M', state='alive', genotype='wt'
        )
        self.source_cage = Cage.objects.create(cage_number="CAGE01", cage_type="TypeA", location="Room 101")
        self.destination_cage = Cage.objects.create(cage_number="CAGE02", cage_type="TypeB", location="Room 102")
        CageHistory.objects.create(mouse_id=self.mouse, cage_id=self.source_cage, start_date=timezone.now())

    def create_request(self, **kwargs):
        """Helper to create a TransferRequest."""
        data = {
            'mouse': self.mouse,
            'source_cage': self.source_cage,
            'destination_cage': self.destination_cage,
            'requester': self.user,
        }
        data.update(kwargs)  # this lets overrides take effect safely
        return TransferRequest.objects.create(**data)

    def test_valid_transfer_request(self):
        """Tests valid TransferRequest creation."""
        request = self.create_request()
        self.assertEqual(request.status, "pending")
        self.assertEqual(request.mouse, self.mouse)
        self.assertEqual(request.source_cage, self.source_cage)
        self.assertEqual(request.destination_cage, self.destination_cage)
        self.assertEqual(request.requester, self.user)

    def test_clean_method_destination_cage_empty(self):
        """Tests clean method raises ValidationError if destination_cage is empty."""
        request = TransferRequest(
            mouse=self.mouse,
            source_cage=self.source_cage,
            destination_cage=None,  # Intentionally invalid
            requester=self.user
        )

        with self.assertRaises(ValidationError):
            request.full_clean() 

    def test_clean_method_same_source_and_destination(self):
        """Tests clean method raises ValidationError if source and destination cages are the same."""
        request = TransferRequest(
            mouse=self.mouse,
            source_cage=self.source_cage,
            destination_cage=self.source_cage,  # Invalid: same cage
            requester=self.user
        )

        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_approve_method(self):
        """Tests approve method updates status and creates CageHistory entries."""
        request = self.create_request()
        request.approve(approver=self.user)
        request.refresh_from_db()
        
        # Check that request status is updated and approval date is set
        self.assertEqual(request.status, "approved")
        self.assertIsNotNone(request.approval_date)
        
        # Check CageHistory entries
        self.assertTrue(CageHistory.objects.filter(mouse_id=self.mouse, end_date__isnull=False).exists())
        self.assertTrue(CageHistory.objects.filter(mouse_id=self.mouse, cage_id=self.destination_cage).exists())

    def test_reject_method(self):
        """Tests reject method updates status to 'rejected'."""
        request = self.create_request()
        request.reject()
        self.assertEqual(request.status, "rejected")

class BreedModelTest(TestCase):
    def setUp(self):
        """Sets up test data for Breed."""
        self.strain = Strain.objects.create(name="C57BL/6")
        self.user = User.objects.create_user(username="breeder", email="breeder@abdn.ac.uk", password="pass1234")
        self.male_mouse = Mouse.objects.create(
            strain=self.strain, tube_id=101, dob="2022-01-01", sex='M', state='alive', genotype='wt'
        )
        self.female_mouse = Mouse.objects.create(
            strain=self.strain, tube_id=102, dob="2022-02-01", sex='F', state='alive', genotype='ht'
        )
        self.cage = Cage.objects.create(cage_number="CAGE01", cage_type="TypeA", location="Room 101")

    def create_breeding(self, **kwargs):
        """Helper to create a Breed instance."""
        return Breed.objects.create(male=self.male_mouse, female=self.female_mouse, cage=self.cage, **kwargs)

    def test_valid_breeding(self):
        """Tests valid Breed creation."""
        breeding = self.create_breeding()
        self.assertEqual(breeding.male, self.male_mouse)
        self.assertEqual(breeding.female, self.female_mouse)
        self.assertEqual(breeding.cage, self.cage)
        self.assertEqual(breeding.start_date.date(), dt.datetime.now().date())  # The start date should be the current date

    def test_end_breeding(self):
        """Tests end_breeding method updates breeding and mouse states."""
        breeding = self.create_breeding()
        breeding.end_breeding()

        # Check that the breeding's end date is set
        self.assertIsNotNone(breeding.end_date)

        # Check that both male and female mice have their state updated to 'alive'
        self.male_mouse.refresh_from_db()
        self.female_mouse.refresh_from_db()
        self.assertEqual(self.male_mouse.state, 'alive')
        self.assertEqual(self.female_mouse.state, 'alive')
    
    def test_str_method(self):
        """Tests the string representation of the Breed instance."""
        breeding = self.create_breeding()
        self.assertEqual(str(breeding), f"Breeding {self.male_mouse.mouse_id} x {self.female_mouse.mouse_id}")

class StrainModelTest(TestCase):
    def setUp(self):
        """Sets up test data for Strain."""
        self.strain = Strain.objects.create(name="StrainA")

    def test_strain_creation(self):
        """Tests that a Strain is created and has the correct name."""
        strain = self.strain
        self.assertEqual(strain.name, "StrainA")

    def test_str_method(self):
        """Tests the string representation of the Strain instance."""
        strain = self.strain
        self.assertEqual(str(strain), "StrainA")

    def test_unique_strain_name(self):
        """Tests that the strain name must be unique."""
        with self.assertRaises(Exception):
            Strain.objects.create(name="StrainA")

class NotificationModelTest(TestCase):
    def setUp(self):
        """Sets up test data for Notification."""
        self.user = User.objects.create_user(username="testuser", email='test@abdn.ac.uk', password="password123")
        self.notification = Notification.objects.create(
            recipient=self.user,
            message="This is a test notification.",
            is_read=False,
            request_type="breeding",
            request_id=1
        )

    def test_notification_creation(self):
        """Tests that a Notification is created and has the correct attributes."""
        notification = self.notification
        self.assertEqual(notification.recipient.username, "testuser")
        self.assertEqual(notification.message, "This is a test notification.")
        self.assertEqual(notification.is_read, False)
        self.assertEqual(notification.request_type, "breeding")
        self.assertEqual(notification.request_id, 1)

    def test_str_method(self):
        """Tests the string representation of the Notification instance."""
        notification = self.notification
        self.assertEqual(str(notification), "Notification for testuser - This is a test notif...")

    def test_is_read_default(self):
        """Tests that the default value for 'is_read' is False."""
        notification = Notification.objects.create(
            recipient=self.user,
            message="New notification",
        )
        self.assertFalse(notification.is_read)

    def test_request_type_optional(self):
        """Tests that request_type and request_id can be None (optional)."""
        notification = Notification.objects.create(
            recipient=self.user,
            message="Test notification without request info"
        )
        self.assertIsNone(notification.request_type)
        self.assertIsNone(notification.request_id)

    def test_mark_as_read(self):
        """Tests that we can mark the notification as read."""
        self.notification.is_read = True
        self.notification.save()
        self.assertTrue(self.notification.is_read)