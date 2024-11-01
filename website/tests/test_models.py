from django.test import TestCase
from website.models import *
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime as dt

class CageModelTest(TestCase):

    def test_create_cage(self):
        cage = Cage.objects.create(cage_number='C001', cage_type='Standard', location='Room 101')
        self.assertEqual(Cage.objects.count(), 1)
        self.assertEqual(cage.cage_number, 'C001')
        self.assertEqual(str(cage), 'C001')

class CageHistoryModelTest(TestCase):

    def setUp(self):
        self.strain = Strain.objects.create(name='Strain A')
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            dob=timezone.now().date(),
            sex='M',
            state='alive'
        )
        self.cage = Cage.objects.create(cage_number='C001', cage_type='Standard', location='Room 101')

    def test_cage_history_creation(self):
        # Create a valid CageHistory instance
        start_date = timezone.now()
        end_date = start_date + timezone.timedelta(days=1)  # end_date is after start_date
        cage_history = CageHistory.objects.create(
            cage_id=self.cage,
            mouse_id=self.mouse,
            start_date=start_date,
            end_date=end_date
        )
        # Check if the CageHistory instance was created correctly
        self.assertEqual(cage_history.cage_id, self.cage)
        self.assertEqual(cage_history.mouse_id, self.mouse)
        self.assertEqual(cage_history.start_date, start_date)
        self.assertEqual(cage_history.end_date, end_date)

    def test_end_date_before_start_date(self):
        # Create a CageHistory instance with end_date before start_date
        start_date = timezone.now()
        end_date = start_date - timezone.timedelta(days=1)  # end_date is before start_date

        with self.assertRaises(ValidationError):
            CageHistory.objects.create(
                cage_id=self.cage,
                mouse_id=self.mouse,
                start_date=start_date,
                end_date=end_date
            )

class UserModelTest(TestCase):

    def test_create_user(self):
        user = User.objects.create_user(
            username='john_doe', 
            first_name="John",
            last_name="Doe",
            email='john_doe@abdn.ac.uk', 
            password='password123',
            role='leader'
        )
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.email, 'john_doe@abdn.ac.uk')
        self.assertEqual(user.role, 'leader')

    def test_email_validation(self):
        user = User(username='invalid_user', email='invalid@invalid.com')
        with self.assertRaises(ValidationError):
            user.full_clean()  # This should trigger the clean method and raise a ValidationError

class TeamModelTests(TestCase):
    def test_create_team(self):
        team = Team.objects.create(name='Team A')
        self.assertEqual(str(team), 'Team A')

class TeamMembershipModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@abdn.ac.uk')
        self.team = Team.objects.create(name='Team A')

    def test_create_team_membership(self):
        membership = TeamMembership.objects.create(user=self.user, team=self.team)
        self.assertEqual(str(membership), f"{self.user.username} - {self.team.name} ({self.user.role})")

    def test_unique_membership(self):
        TeamMembership.objects.create(user=self.user, team=self.team)
        with self.assertRaises(ValidationError):
            duplicate_membership = TeamMembership(user=self.user, team=self.team)
            duplicate_membership.full_clean()  # This should raise a validation error

class MouseKeeperModelTests(TestCase):
    def setUp(self):
        self.mouse = Mouse.objects.create(
            strain=Strain.objects.create(name='Strain A'),
            tube_id=1,
            dob=dt.date(2023, 1, 1),
            sex='M',
            state='alive'
        )
        self.user = User.objects.create_user(username='testuser', password='testpass', email='test@abdn.ac.uk')
        self.team = Team.objects.create(name='Team A')

    def test_create_mouse_keeper_with_user(self):
        keeper = MouseKeeper.objects.create(mouse=self.mouse, user=self.user, start_date=dt.date(2023, 1, 1),)
        self.assertEqual(str(keeper), f"Mouse {self.mouse.mouse_id} - Keeper {self.user}")

    def test_create_mouse_keeper_with_team(self):
        keeper = MouseKeeper.objects.create(mouse=self.mouse, team=self.team, start_date=dt.date(2023, 1, 1),)
        self.assertEqual(str(keeper), f"Mouse {self.mouse.mouse_id} - Keeper {self.team}")

    def test_clean_method_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            keeper = MouseKeeper(mouse=self.mouse, user=self.user, team=self.team, start_date=dt.date(2023, 1, 1),)
            keeper.full_clean()  # Should raise validation error for both user and team being set

class MouseModelTest(TestCase):

    def setUp(self):
        # Create required related objects (strain, user)
        self.strain = Strain.objects.create(name='C57BL/6')
        self.user = User.objects.create_user(username='mouse_keeper', first_name='John', last_name='Doe', email='keeper@abdn.ac.uk', password='pass123', role='leader')

    def test_create_mouse(self):
        mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=101,
            dob=dt.date(2023, 1, 1),
            sex='M',
            state='alive',
        )
        self.assertEqual(Mouse.objects.count(), 1)
        self.assertEqual(mouse.state, 'alive')
        self.assertEqual(str(mouse), f"Mouse {mouse.mouse_id} - {self.strain} - Tube 101")

    def test_mouse_ancestors_descendants(self):
        mother = Mouse.objects.create(strain=self.strain, tube_id=1, dob=dt.date(2020, 1, 1), sex='F', state='alive')
        father = Mouse.objects.create(strain=self.strain, tube_id=2, dob=dt.date(2020, 1, 1), sex='M', state='alive')
        child = Mouse.objects.create(strain=self.strain, tube_id=3, dob=dt.date(2023, 1, 1), sex='M', state='alive', mother=mother, father=father)

        self.assertIn(mother, child.get_ancestors())
        self.assertIn(father, child.get_ancestors())
        self.assertIn(child, mother.get_descendants())
        self.assertIn(child, father.get_descendants())

class WeightModelTests(TestCase):
    def setUp(self):
        self.mouse = Mouse.objects.create(
            strain=Strain.objects.create(name='Strain A'),
            tube_id=1,
            dob=dt.date(2023, 1, 1),
            sex='M',
            state='alive'
        )

    def test_create_weight(self):
        weight = Weight.objects.create(mouse=self.mouse, weight=25.5)
        self.assertEqual(weight.weight, 25.5)

class ProjectModelTests(TestCase):
    def test_create_project(self):
        project = Project.objects.create(
            description="Sample Project",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.assertEqual(str(project.description), "Sample Project")

    def test_project_end_date_optional(self):
        project = Project.objects.create(
            description="Project without end date",
            start_date=timezone.now()
        )
        self.assertIsNone(project.end_date)

class ProjectMouseModelTests(TestCase):
    def setUp(self):
        self.strain = Strain.objects.create(name='Strain A')
        self.project = Project.objects.create(
            description="Sample Project",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            dob=timezone.now().date(),
            sex='M',
            state='alive'
        )

    def test_create_project_mouse(self):
        project_mouse = ProjectMouse.objects.create(project_id=self.project, mouse_id=self.mouse)
        self.assertEqual(project_mouse.project_id, self.project)
        self.assertEqual(project_mouse.mouse_id, self.mouse)

    def test_unique_together_constraint(self):
        ProjectMouse.objects.create(project_id=self.project, mouse_id=self.mouse)
        with self.assertRaises(ValidationError):
            duplicate_project_mouse = ProjectMouse(project_id=self.project, mouse_id=self.mouse)
            duplicate_project_mouse.full_clean()  # This should raise a validation error

class ProjectUserModelTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            description="Sample Project",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30)
        )
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            email='test@abdn.ac.uk'
        )

    def test_create_project_user(self):
        project_user = ProjectUser.objects.create(project_id=self.project, user_id=self.user)
        self.assertEqual(project_user.project_id, self.project)
        self.assertEqual(project_user.user_id, self.user)

    def test_unique_together_constraint(self):
        ProjectUser.objects.create(project_id=self.project, user_id=self.user)
        with self.assertRaises(ValidationError):
            duplicate_project_user = ProjectUser(project_id=self.project, user_id=self.user)
            duplicate_project_user.full_clean()

class RequestModelTest(TestCase):

    def setUp(self):
        self.strain = Strain.objects.create(name='C57BL/6')
        self.user = User.objects.create_user(username='requester', email='requester@abdn.ac.uk', password='pass123')
        self.cage = Cage.objects.create(cage_number='C001', cage_type='Breeding', location='Room 101')
        self.mouse_male = Mouse.objects.create(strain=self.strain, tube_id=101, dob=dt.date(2023, 1, 1), sex='M', state='alive')
        self.mouse_female = Mouse.objects.create(strain=self.strain, tube_id=102, dob=dt.date(2023, 1, 1), sex='F', state='alive')

    def test_breeding_request(self):
        # Valid breeding request
        request = Request.objects.create(
            requester=self.user,
            mouse=self.mouse_male,
            second_mouse=self.mouse_female,
            cage=self.cage,
            request_type='breed'
        )
        request.full_clean()  # Should pass validation
        self.assertEqual(Request.objects.count(), 1)

    def test_invalid_breeding_request(self):
        # Breeding request with same-sex mice
        request = Request(
            requester=self.user,
            mouse=self.mouse_male,
            second_mouse=self.mouse_male,  # Same sex
            cage=self.cage,
            request_type='breed'
        )
        with self.assertRaises(ValidationError):
            request.full_clean()

    def test_culling_request(self):
        # Valid culling request
        cull_request = Request.objects.create(
            requester=self.user,
            mouse=self.mouse_male,
            request_type='cull'
        )
        cull_request.full_clean()  # Should pass validation
        self.assertEqual(Request.objects.count(), 1)

    def test_invalid_culling_request(self):
        # Culling request with a second mouse (shouldn't have one)
        cull_request = Request(
            requester=self.user,
            mouse=self.mouse_male,
            second_mouse=self.mouse_female,
            request_type='cull'
        )
        with self.assertRaises(ValidationError):
            cull_request.full_clean()

class BreedModelTest(TestCase):

    def setUp(self):
        self.strain = Strain.objects.create(name='C57BL/6')
        self.cage = Cage.objects.create(cage_number='C001', cage_type='Breeding', location='Room 101')
        self.male = Mouse.objects.create(strain=self.strain, tube_id=101, dob=dt.date(2023, 1, 1), sex='M', state='alive')
        self.female = Mouse.objects.create(strain=self.strain, tube_id=102, dob=dt.date(2023, 1, 1), sex='F', state='alive')

    def test_breed_creation(self):
        breed = Breed.objects.create(male=self.male, female=self.female, cage=self.cage)
        self.assertEqual(Breed.objects.count(), 1)
        self.assertEqual(str(breed), f"Breeding {self.male.mouse_id} x {self.female.mouse_id}")
        
    def test_end_breeding(self):
        breed = Breed.objects.create(male=self.male, female=self.female, cage=self.cage)
        breed.end_breeding()
        self.assertIsNotNone(breed.end_date)
        self.assertEqual(self.male.state, 'alive')
        self.assertEqual(self.female.state, 'alive')

class StrainModelTest(TestCase):

    def test_create_strain(self):
        strain = Strain.objects.create(name='C57BL/6')
        self.assertEqual(Strain.objects.count(), 1)
        self.assertEqual(str(strain), 'C57BL/6')

class GenotypeModelTest(TestCase):

    def setUp(self):
        self.strain = Strain.objects.create(name='C57BL/6')
        self.mouse = Mouse.objects.create(strain=self.strain, tube_id=101, dob=dt.date(2023, 1, 1), sex='M', state='alive')

    def test_create_genotype(self):
        genotype = Genotype.objects.create(
            mouse=self.mouse,
            gene='p53',
            allele_1='A',
            allele_2='B'
        )
        self.assertEqual(Genotype.objects.count(), 1)
        self.assertEqual(str(genotype), f"{self.mouse.mouse_id} - p53: A/B")

class PhenotypeModelTest(TestCase):

    def setUp(self):
        self.strain = Strain.objects.create(name='C57BL/6')
        self.mouse = Mouse.objects.create(strain=self.strain, tube_id=101, dob=dt.date(2023, 1, 1), sex='M', state='alive')

    def test_create_phenotype(self):
        phenotype = Phenotype.objects.create(
            mouse=self.mouse,
            characteristic='Coat Color',
            description='Black'
        )
        self.assertEqual(Phenotype.objects.count(), 1)
        self.assertEqual(str(phenotype), f"{self.mouse.mouse_id} - Coat Color: Black")