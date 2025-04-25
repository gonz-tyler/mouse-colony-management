from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.utils import timezone
from django.http import JsonResponse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q

from website.models import *
from website.forms import *
from website.views import *

import json
import logging
from datetime import date, datetime

User = get_user_model()

class LegalViewsTest(TestCase):
    def setUp(self):
        self.client = RequestFactory()

    def test_terms_of_service_view(self):
        """
        Test case for the 'terms_of_service' view.
        This test ensures that the 'terms_of_service' view is accessible via
        the correct URL and returns a successful HTTP 200 status code.
        Steps:
        - Perform a GET request to the 'terms_of_service' URL.
        - Verify that the response status code is 200.
        """
        response = self.client.get(reverse('terms_of_service'))
        response = terms_of_service(response)
        self.assertEqual(response.status_code, 200)

    def test_privacy_policy_view(self):
        """
        Test case for the privacy policy view.
        This test ensures that the privacy policy view is accessible and returns
        a successful HTTP 200 status code when accessed via the client.
        """
        response = self.client.get(reverse('privacy_policy'))
        response = privacy_policy(response)
        self.assertEqual(response.status_code, 200)

class AuthViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123'
        )
        self.factory = RequestFactory()
        
    def add_session_and_auth_to_request(self, request):
        """Add session and authentication to the request"""
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()
        
        auth_middleware = AuthenticationMiddleware(lambda req: None)
        auth_middleware.process_request(request)
        return request

    def test_login_required_home_view(self):
        """
        Test case for verifying that the home view requires user authentication.
        This test simulates an unauthenticated user attempting to access the home view.
        It ensures that the view redirects to the login page when accessed by an 
        unauthenticated user.
        """
        # Create a GET request
        request = self.factory.get(reverse('index'))
        request.user = AnonymousUser()  # Unauthenticated user
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = home_view(request)
        self.assertEqual(response.status_code, 302)  # Should redirect to login

    def test_home_view_authenticated(self):
        """
        Test the home view for an authenticated user.
        This test verifies that when an authenticated user accesses the home view
        via a GET request, the response has a status code of 302 (redirect).
        """

        # Create a GET request
        request = self.factory.get(reverse('index'))
        request.user = self.user  # Authenticated user
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = home_view(request)
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """
        Test case for the logout view.
        This test verifies that the logout view correctly handles a GET request
        from an authenticated user. It ensures that the user is logged out and
        the response redirects to the appropriate location.
        """

        # Create a GET request
        request = self.factory.get(reverse('logout_user'))
        request.user = self.user  # Authenticated user
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = logout_user(request)
        self.assertEqual(response.status_code, 302)  # Should redirect after logout

    def test_register_view_get(self):
        """
        Test the GET request to the register view, ensuring it returns a 200 status code.
        """

        # Create a GET request
        request = self.factory.get(reverse('register'))
        request.user = AnonymousUser()
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = register(request)
        self.assertEqual(response.status_code, 200)

    def test_register_view_post_valid(self):
        """
        Test the register view with a valid POST request.
        Ensures that a new user is successfully created and the response
        redirects as expected.
        """

        # Create a POST request with valid data
        data = {
            'username': 'newuser',
            'email': 'new@abdn.ac.uk',
            'password1': 'ComplexPassword123!',
            'password2': 'ComplexPassword123!',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'staff'
        }
        request = self.factory.post(reverse('register'), data)
        request.user = AnonymousUser()
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = register(request)
        self.assertEqual(response.status_code, 302)  # Should redirect after registration
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_profile_view(self):
        """
        Test the user_profile view to ensure it redirects with a 302 status code.
        """
        # Create a GET request
        request = self.factory.get(reverse('user_profile', args=[self.user.username]))
        request.user = self.user
        
        # Add session middleware
        request = self.add_session_and_auth_to_request(request)
        
        # Call the view directly
        response = user_profile(request, self.user.username)
        self.assertEqual(response.status_code, 302)

class ProfileViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123'
        )
        self.client.force_login(self.user)

    def test_edit_profile_view_get(self):
        """
        Test the GET request for the edit_profile view to ensure it returns a 200 status code.
        """

        response = self.client.get(reverse('edit_profile'))
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_view_post_valid(self):
        """
        Test the edit profile view with valid POST data, ensuring the user profile is updated
        and the response redirects as expected.
        """

        data = {
            'username': 'updateduser',
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@abdn.ac.uk'
        }
        response = self.client.post(reverse('edit_profile'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect after update
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'updateduser')

    def test_delete_account_view(self):
        """
        Test the delete_account view to ensure it redirects after account deletion
        and the user is removed from the database.
        """

        response = self.client.post(reverse('delete_account'))
        self.assertEqual(response.status_code, 302)  # Should redirect after deletion
        self.assertFalse(User.objects.filter(username='testuser').exists())

class NotificationViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123'
        )
        self.notification = Notification.objects.create(
            recipient=self.user,
            message='Test notification',
            created_at=timezone.now()
        )
        self.client.force_login(self.user)

    def test_notifications_view(self):
        """
        Test the notifications view to ensure it returns a 200 status code,
        contains the expected notification text, and includes the correct
        notifications in the context.
        """

        response = self.client.get(reverse('notifications', args=[self.user.username]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test notification')  # Check notification appears in response
        self.assertEqual(list(response.context['notifications']), [self.notification])

    def test_mark_notification_as_read(self):
        """
        Test the functionality of marking a notification as read.
        Ensures the view redirects successfully and updates the notification's
        status to read in the database.
        """

        url = reverse('mark_notification_as_read', kwargs={'username': self.notification.recipient.username, 'notification_id': self.notification.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_delete_notification(self):
        """
        Test the deletion of a notification.
        Ensures the notification is deleted and the response redirects.
        """

        url = reverse('delete_notification', args=[self.notification.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Should redirect
        self.assertFalse(Notification.objects.filter(id=self.notification.id).exists())

class MouseViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123',
            role='leader'
        )
        self.strain = Strain.objects.create(name='Test Strain')
        self.mouse = Mouse.objects.create(
            tube_id=1,
            sex='M',
            state='alive',
            strain=self.strain,
            dob=date.today(),
        )
        self.client.force_login(self.user)
        self.team = Team.objects.create(name='Test Team')

    def test_view_mouse(self):
        """
        Test the 'view_mouse' view to ensure it returns a 200 status code
        and the correct mouse object in the context.
        """

        response = self.client.get(reverse('view_mouse', args=[self.mouse.mouse_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['mouse'], self.mouse)

    def test_add_mouse_get(self):
        """
        Test the GET request for the 'add_mouse' view.
        Ensures the response status is 200 and the context contains an AddMouseForm instance.
        """

        response = self.client.get(reverse('add_mouse'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AddMouseForm)

    def test_add_mouse_post_valid(self):
        """
        Test the POST request to add a new mouse with valid data.
        Ensures the mouse is created and a redirect occurs.
        """

        data = {
            'tube_id': 2,
            'dob': date.today(),
            'sex': 'F',
            'state': 'alive',
            'strain': self.strain.id,
            'genotype': 'wt'
        }
        response = self.client.post(reverse('add_mouse'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Mouse.objects.filter(tube_id=2).exists())

    def test_delete_mouse(self):
        """
        Test the deletion of a mouse by a user with the 'leader' role.
        Ensures the mouse is removed and a redirect occurs.
        """

        # Need to be a leader to delete
        self.user.role = 'leader'
        self.user.save()
        
        response = self.client.post(reverse('delete_mouse', args=[self.mouse.mouse_id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Mouse.objects.filter(mouse_id=self.mouse.mouse_id).exists())

    def test_genetic_tree_view(self):
        """
        Test the genetic_tree view to ensure it returns a 200 status code 
        and includes 'tree_data' and 'mouse' in the context.
        """

        response = self.client.get(reverse('genetic_tree', args=[self.mouse.mouse_id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('tree_data', response.context)
        self.assertIn('mouse', response.context)

class TeamViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123',
            role='leader',
        )
        self.team = Team.objects.create(name='Test Team')
        TeamMembership.objects.create(user=self.user, team=self.team)
        self.client.force_login(self.user)

    def test_all_teams_view(self):
        """
        Test the 'teams' view to ensure it returns a 200 status code, 
        includes 'user_teams' and 'other_teams' in the context, 
        and verifies the correct data in 'user_teams'.
        """

        response = self.client.get(reverse('teams'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_teams', response.context)
        self.assertIn('other_teams', response.context)
        self.assertEqual(len(response.context['user_teams']), 1)
        self.assertEqual(response.context['user_teams'][0], self.team)

    def test_team_details_view(self):
        """
        Test the team_details view to ensure it returns a 200 status code,
        provides the correct team context, and verifies membership and leadership status.
        """

        response = self.client.get(reverse('team_details', args=[self.team.name]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['team'], self.team)
        self.assertTrue(response.context['is_member'])
        self.assertTrue(response.context['is_leader'])

    def test_join_team(self):
        """
        Test the functionality of joining a team.
        Ensures that a user can successfully join a team and that the 
        appropriate team membership is created.
        """

        new_team = Team.objects.create(name='New Team')
        request = self.client.get(reverse('join_team', args=[new_team.name]))
        request.user = self.user
        response = TeamClass.join_team(request, new_team.name)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TeamMembership.objects.filter(user=self.user, team=new_team).exists())

    def test_leave_team(self):
        """
        Test the leave_team view to ensure a user can successfully leave a team,
        resulting in a redirect and removal of the user's team membership.
        """
        
        request = self.client.get(reverse('leave_team', args=[self.team.name]))
        request.user = self.user
        response = TeamClass.leave_team(request, self.team.name)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TeamMembership.objects.filter(user=self.user, team=self.team).exists())

    def test_create_team_view_get(self):
        """
        Tests the GET request for the 'create_team' view, ensuring the page loads successfully
        and contains the expected content.
        """

        response = self.client.get(reverse('create_team'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Team') 

    def test_create_team_view_post(self):
        """
        Test the POST request to create a new team.
        Verifies that a new team is created, the user is added as a member,
        and the response redirects successfully.
        """

        data = {
            'name': 'New Team',
            'members': [self.user.id]  # Include current user as member
        }
        response = self.client.post(reverse('create_team'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect after creation
        self.assertTrue(Team.objects.filter(name='New Team').exists())
        self.assertTrue(TeamMembership.objects.filter(team__name='New Team', user=self.user).exists())

class CageViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123'
        )
        self.cage = Cage.objects.create(cage_id=1, cage_type='breeding')
        self.strain = Strain.objects.create(name='Test Strain')
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            sex='M',
            state='alive',
            dob=date.today(),
        )
        self.client.force_login(self.user)

    def test_all_cages_view(self):
        """
        Test the 'all cages' view to ensure it returns a 200 status code 
        and includes 'cage_data' in the response context.
        """

        response = self.client.get(reverse('cages'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('cage_data', response.context)

    def test_cage_details_view(self):
        """
        Test the cage details view to ensure it returns a 200 status code
        and the correct cage context data.
        """

        response = self.client.get(reverse('cage_details', args=[self.cage.cage_id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['cage'], self.cage)

    def test_add_mouse_to_cage(self):
        """
        Test adding a mouse to a cage and verify the operation is successful.
        """

        response = self.client.post(reverse('add_mouse_to_cage', args=[self.cage.cage_id]), 
                                  {'mouse_id': self.mouse.mouse_id})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CageHistory.objects.filter(mouse_id=self.mouse, cage_id=self.cage).exists())

    def test_fetch_available_mice(self):
        """
        Test the fetch_available_mice view to ensure it returns a 200 status code 
        and a JsonResponse when called via AJAX with a valid cage_id.
        """

        response = self.client.get(
            reverse('fetch_available_mice'),
            {'cage_id': self.cage.cage_id},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # Simulate AJAX
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response, JsonResponse)

class RequestViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123',
            role='leader'
        )
        self.breeder = User.objects.create_user(
            username='breeder',
            email='breeder@abdn.ac.uk',
            password='testpass123',
            role='breeder'
        )
        self.strain = Strain.objects.create(name='Test Strain')
        self.mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            sex='M',
            state='alive',
            dob=date.today(),
        )
        self.mouse2 = Mouse.objects.create(
            strain=self.strain,
            tube_id=2,
            sex='F',
            state='alive',
            dob=date.today(),
        )
        self.cage = Cage.objects.create(cage_id=1, cage_type='standard')
        self.transfer_request = TransferRequest.objects.create(
            requester=self.user,
            mouse=self.mouse,
            source_cage=self.cage,
            destination_cage=self.cage,
            status='pending'
        )
        self.breeding_request = BreedingRequest.objects.create(
            requester=self.user,
            male_mouse=self.mouse,
            female_mouse=self.mouse2,
            cage=self.cage,
            status='pending'
        )
        self.culling_request = CullingRequest.objects.create(
            requester=self.user,
            mouse=self.mouse,
            status='pending'
        )
        self.client.force_login(self.user)

    def test_all_requests_view(self):
        """
        Test the 'all_requests' view to ensure it returns a 200 status code
        and includes 'current_transfers' in the context.
        """

        response = self.client.get(reverse('all_requests'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('current_transfers', response.context)

    def test_create_transfer_request_view(self):
        """
        Test the 'create_transfer_request' view to ensure it returns a 200 status code.
        """

        response = self.client.get(reverse('create_transfer_request'))
        self.assertEqual(response.status_code, 200)

    def test_approve_transfer_request(self):
        """
        Test the approval of a transfer request by a breeder, ensuring the request
        status is updated to 'completed' and a redirect response is returned.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('approve_transfer', args=[self.transfer_request.id]))
        self.assertEqual(response.status_code, 302)
        self.transfer_request.refresh_from_db()
        self.assertEqual(self.transfer_request.status, 'completed')

    def test_reject_transfer_request(self):
        """
        Test that a transfer request is successfully rejected and its status is updated.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('reject_transfer', args=[self.transfer_request.id]))
        self.assertEqual(response.status_code, 302)
        self.transfer_request.refresh_from_db()
        self.assertEqual(self.transfer_request.status, 'rejected')

    def test_cancel_transfer_request(self):
        """
        Test that a transfer request is successfully canceled and deleted.
        """

        response = self.client.get(reverse('cancel_transfer_request', args=[self.transfer_request.id]))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(TransferRequest.DoesNotExist):
            TransferRequest.objects.get(id=self.transfer_request.id)

    def test_create_breeding_request_view(self):
        """
        Tests the 'create_breeding_request' view to ensure it returns a 200 status code.
        """

        response = self.client.get(reverse('create_breeding_request'))
        self.assertEqual(response.status_code, 200)

    def test_approve_breeding_request(self):
        """
        Test the approval of a breeding request, ensuring the status is updated
        and the response redirects as expected.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('approve_breeding', args=[self.breeding_request.id]))
        self.assertEqual(response.status_code, 302)
        self.breeding_request.refresh_from_db()
        self.assertEqual(self.breeding_request.status, 'completed')

    def test_reject_breeding_request(self):
        """
        Test that a breeding request can be successfully rejected, updating its status
        and redirecting the user.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('reject_breeding', args=[self.breeding_request.id]))
        self.assertEqual(response.status_code, 302)
        self.breeding_request.refresh_from_db()
        self.assertEqual(self.breeding_request.status, 'rejected')

    def test_cancel_breeding_request(self):
        """
        Test that a breeding request is successfully canceled and deleted.
        """

        response = self.client.get(reverse('cancel_breeding_request', args=[self.breeding_request.id]))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(BreedingRequest.DoesNotExist):
            BreedingRequest.objects.get(id=self.breeding_request.id)

    def test_create_culling_request_view(self):
        """
        Test the view for creating a culling request to ensure it returns a 200 status code.
        """

        response = self.client.get(reverse('create_culling_request'))
        self.assertEqual(response.status_code, 200)

    def test_approve_culling_request(self):
        """
        Test the approval of a culling request by verifying the response status 
        and the updated status of the culling request in the database.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('approve_culling', args=[self.culling_request.id]))
        self.assertEqual(response.status_code, 302)
        self.culling_request.refresh_from_db()
        self.assertEqual(self.culling_request.status, 'completed')

    def test_reject_culling_request(self):
        """
        Test that a culling request is successfully rejected and its status is updated.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('reject_culling', args=[self.culling_request.id]))
        self.assertEqual(response.status_code, 302)
        self.culling_request.refresh_from_db()
        self.assertEqual(self.culling_request.status, 'rejected')

    def test_cancel_culling_request(self):
        """
        Test that a culling request is successfully canceled and the object is deleted.
        """

        response = self.client.get(reverse('cancel_culling_request', args=[self.culling_request.id]))
        self.assertEqual(response.status_code, 302)
        with self.assertRaises(CullingRequest.DoesNotExist):
            CullingRequest.objects.get(id=self.culling_request.id)

class BreedingViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@abdn.ac.uk',
            password='testpass123',
            role='leader'
        )
        self.breeder = User.objects.create_user(
            username='breeder',
            email='breeder@abdn.ac.uk',
            password='testpass123',
            role='breeder'
        )
        self.strain = Strain.objects.create(name='Test Strain')
        self.male_mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=1,
            sex='M',
            state='alive',
            dob=date.today(),
        )
        self.female_mouse = Mouse.objects.create(
            strain=self.strain,
            tube_id=2,
            sex='F',
            state='alive',
            dob=date.today(),
        )
        self.cage = Cage.objects.create(cage_id=1, cage_type='breeding')
        self.breeding = Breed.objects.create(
            male=self.male_mouse,
            female=self.female_mouse,
            cage=self.cage,
            start_date=timezone.now()
        )
        self.client.force_login(self.user)

    def test_all_breedings_view(self):
        """
        Test the 'all_breedings' view to ensure it returns a 200 status code 
        and includes 'current_breedings' in the context.
        """

        response = self.client.get(reverse('all_breedings'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('current_breedings', response.context)

    def test_end_breeding(self):
        """
        Test the 'end_breeding' view to ensure it sets the end date for a breeding 
        and redirects successfully.
        """

        self.client.force_login(self.breeder)
        response = self.client.get(reverse('end_breeding', args=[self.breeding.breed_id]))
        self.assertEqual(response.status_code, 302)
        self.breeding.refresh_from_db()
        self.assertIsNotNone(self.breeding.end_date)

class UserManagementViewsTest(TestCase):
    def setUp(self):
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@abdn.ac.uk',
            password='testpass123',
            role='leader'
        )
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@abdn.ac.uk',
            password='testpass123',
            role='staff'
        )
        self.client.force_login(self.leader)

    def test_manage_users_view(self):
        """
        Test the manage_users view to ensure it returns a 200 status code
        and includes 'users' in the response context.
        """

        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('users', response.context)

    def test_update_user_role(self):
        """
        Test the update_user_role view to ensure it updates a user's role
        and redirects successfully.
        """

        response = self.client.post(reverse('update_user_role', args=[self.staff.id]), 
                                  {'role': 'new_staff'})
        self.assertEqual(response.status_code, 302)
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, 'new_staff')

    def test_update_user_role_forbidden(self):
        """
        Test that updating a user's role is forbidden for non-leader users.
        """

        self.client.force_login(self.staff)
        # Attempt to update the role as a non-leader
        response = self.client.post(reverse('update_user_role', args=[self.staff.id]), 
                                  {'role': 'new_staff'})
        self.assertEqual(response.status_code, 403)  # Should be forbidden for non-leader
        self.staff.refresh_from_db()
        self.assertEqual(self.staff.role, 'staff')

class PasswordResetViewsTest(TestCase):
    def setUp(self):
        self.client.force_login(User.objects.create_user(
            username='testuser',
            email='tes@abdn.ac.uk',
            password='testpass123',
            role='staff'
        ))

    def test_password_reset_view(self):
        response = self.client.get(reverse('password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_done_view(self):
        response = self.client.get(reverse('password_reset_done'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_confirm_view(self):
        response = self.client.get(reverse('password_reset_confirm', args=['uidb64', 'token']))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_complete_view(self):
        response = self.client.get(reverse('password_reset_complete'))
        self.assertEqual(response.status_code, 200)