import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .decorators import role_required
from .models import *
from .forms import *
import json

from django.views.generic.edit import UpdateView
from django.contrib.auth.forms import PasswordResetForm

# --- Messages ---
record_added = "Record has been added successfully."
record_deleted = "Record has been deleted successfully."
record_updated = "Record has been updated successfully."

# Legal Boiler-plate Views
def terms_of_service(request):
    return render(request, 'legal/terms-of-service.html')
def privacy_policy(request):
    return render(request, 'legal/privacy-policy.html')

def password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)  # Sends the email with reset link
            return redirect('password_reset_done')  # Redirect to done page
    else:
        form = PasswordResetForm()
    
    return render(request, 'registration/password_reset_form.html', {'form': form})
def password_reset_done(request):
    return render(request, 'registration/password_reset_done.html')
def password_reset_confirm(request):
    return render(request, 'registration/password_reset_confirm.html')
def password_reset_complete(request):
    return render(request, 'registration/password_reset_complete.html')



@login_required
def home_view(request):
    # Debugging: Log the page number
    page_number = request.GET.get('page', 1)
    logging.debug(f"Requested page number: {page_number}")
    # Fetch only the Mouse records that belong to the logged-in user
    mice = Mouse.mice_managed_by_user(request.user).order_by("tube_id")
    paginator = Paginator(mice, 10)  # Show 10 users per page
    # Get the page number from the request (default to 1)
    page_number = request.GET.get('page')
    
    # Ensure the page number is valid, otherwise default to 1
    try:
        page_number = int(page_number) if page_number is not None else 1
        if page_number < 1:
            page_number = 1
    except (ValueError, TypeError):  # Catch invalid page number (e.g., 'abc' or None)
        page_number = 1  # Default to the first page if invalid

    # Paginate the query
    try:
        page_obj = paginator.get_page(page_number)
    except EmptyPage:
        page_obj = paginator.get_page(paginator.num_pages)  # Fallback to the last page if page number is too high
    return render(request, 'home.html', {'page_obj': page_obj})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out...")
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('index')  # Redirect to homepage
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def user_profile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'registration/profile.html', {"user": user})

# DELETE ACCOUNT
@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user

        # Prevent deletion of superuser accounts
        if user.is_superuser:
            messages.error(request, "Admin accounts cannot be deleted.")
            return render(request, 'registration/profile.html', {"user": user})

        logout(request)  # Log the user out
        user.delete()  # Delete the user account
        messages.success(request, "Your account has been deleted successfully.")
        return redirect('index')
    return render(request, 'registration/profile.html', {"user": user})

@login_required
def edit_profile(request):
    user = request.user
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('user_profile', username=request.user.username)
    else:
        form = ProfileUpdateForm(instance=user)

    context = {
        'form': form,
    }
    return render(request, 'registration/edit_profile.html', context)

# Generate genetic tree
def genetic_tree(request, mouse_id):
    mouse = get_object_or_404(Mouse, mouse_id=mouse_id)
    
    # Recursive function to get only parents and their parents recursively
    def get_direct_ancestor_structure(mouse):
        # Assuming `get_parents()` is a method that fetches direct parents only
        ancestors = []
        for parent in mouse.get_parents():  # Replace with actual logic to get parents
            ancestors.append({
                'name': f"Strain {parent.strain} - TubeID {parent.tube_id}",
                'children': get_direct_ancestor_structure(parent)
            })
        return ancestors

    tree_data = {
        'name': f"Strain {mouse.strain} - TubeID {mouse.tube_id}",
        'children': get_direct_ancestor_structure(mouse)
    }

    return render(request, 'genetictree.html', {'tree_data': json.dumps(tree_data), 'mouse': mouse})

@login_required
def manage_users(request):
    """Allow lead users to manage other users' roles."""
    if not request.user.role == 'leader':  # Ensure only leads can access
        messages.error(request, "You do not have permission to access this page.")
        return redirect('index')

    # Fetch all users excluding breeding users and other lead users
    users = User.objects.exclude(role='breeder').exclude(role='leader')

    return render(request, 'management/manage_users.html', {'users': users})


@login_required
def update_user_role(request, user_id):
    """Update user roles (only allowed by lead users)."""
    if request.method == "POST":
        if not request.user.role == 'leader':  # Ensure only leads can change roles
            messages.success(request, "You do not have permission to perform this action.")
            return redirect('index')

        user = get_object_or_404(User, id=user_id)

        # Prevent changing roles of other leads
        if user.role == 'leader':
            messages.success(request, "You do not have permission to access this page.")
            return redirect('manage_users')

        new_role = request.POST.get('role')
        if new_role in ['new_staff', 'staff']:  # Ensure only allowed roles
            user.role = new_role
            user.save()
            messages.success(request, f"Role successfully updated to {new_role}.")
            return redirect('manage_users')

        messages.error(request, "Invalid role selected.")
        return redirect('manage_users')

    messages.error(request, "Invalid request.")
    return redirect('manage_users')


class MouseClass:
    @login_required
    @role_required(allowed_roles=['leader', 'staff', 'new_staff'])
    def view_mouse(request, mouse_id):
        if request.user.is_authenticated:
            #look up mouse
            mouse = Mouse.objects.get(mouse_id=mouse_id)
            return render(request, 'mice/mouse_details.html', {'mouse':mouse})
        else:
            messages.success(request, 'You must be logged in to view this page.')
            return redirect('index')

    @login_required
    @role_required(allowed_roles=['leader', 'staff'])
    def add_mouse(request):
        if request.method == 'POST':
            form = AddMouseForm(request.POST, user=request.user)  # Pass the user
            if form.is_valid():
                # Save the mouse object
                mouse = form.save()

                # Create MouseKeeper entry
                team = form.cleaned_data.get('team')
                if team:
                    # If a team is specified, connect the mouse to the team
                    MouseKeeper.objects.create(mouse=mouse, team=team, start_date=timezone.now())
                else:
                    # Otherwise, connect the mouse to the logged-in user
                    MouseKeeper.objects.create(mouse=mouse, user=request.user, start_date=timezone.now())

                return redirect('index')  # Redirect to a view showing the list of mice
        else:
            form = AddMouseForm(user=request.user)  # Pass the user
        
        return render(request, 'mice/add_mouse.html', {'form': form})

    
    class MouseUpdateView(UpdateView):
        model = Mouse
        form_class = AddMouseForm
        template_name = 'mice/update_mouse.html'
        pk_url_kwarg = 'mouse_id'  # Use pk_url_kwarg to identify the primary key in the URL
        success_url = '/'  # Redirect URL after successful update

        # Decorate the dispatch method to apply role_required
        @method_decorator(role_required(allowed_roles=['leader', 'staff']))
        def dispatch(self, *args, **kwargs):
            return super().dispatch(*args, **kwargs)
    
    @login_required
    @role_required(allowed_roles=['leader'])
    def delete_mouse(request, mouse_id):
        delete_it = Mouse.objects.get(mouse_id=mouse_id)
        delete_it.delete()
        messages.success(request, record_deleted)
        return redirect('index')
    
class StrainClass:
    def create_strain(request):
        """Handles creating a new strain via AJAX."""
        if request.method == 'POST':
            new_strain_name = request.POST.get('new_strain')
            if new_strain_name:
                # Create the new strain
                strain = Strain.objects.create(name=new_strain_name)
                return JsonResponse({
                    'success': True,
                    'strain_id': strain.id,
                    'strain_name': strain.name
                })
            else:
                return JsonResponse({'success': False}, status=400)

        return JsonResponse({'success': False}, status=400)

class TeamClass:
    @login_required
    def all_teams(request):
        # Fetch all teams with prefetch for users
        teams = Team.objects.prefetch_related('teammembership_set__user')

        # Get names of teams the user is a member of
        user_team_names = TeamMembership.objects.filter(user=request.user).values_list('team__name', flat=True)

        # Separate user and other teams
        user_teams = [team for team in teams if team.name in user_team_names]
        other_teams = [team for team in teams if team.name not in user_team_names]

        return render(request, 'team/all_teams.html', {
            'user_teams': user_teams,
            'other_teams': other_teams
        })
    
    @login_required
    def join_team(request, team_name):
        team = Team.objects.get(name=team_name)
        TeamMembership.objects.get_or_create(user=request.user, team=team)
        return redirect('team_details', team_name=team.name)
    
    @login_required
    def team_details(request, team_name):
        team = get_object_or_404(Team, name=team_name)
        is_member = TeamMembership.objects.filter(team=team, user=request.user).exists()
        is_leader = request.user.role == 'leader'

        context = {
            'team': team,
            'is_member': is_member,
            'is_leader': is_leader
        }
        return render(request, 'team/team_details.html', context)

    @login_required
    def leave_team(request, team_name):
        team = get_object_or_404(Team, name=team_name)
        TeamMembership.objects.filter(user=request.user, team=team).delete()
        return redirect('teams')

    @login_required
    @role_required(allowed_roles=['leader'])
    def delete_team(request, team_name):
        team = get_object_or_404(Team, name=team_name)
        team.delete()
        return redirect('teams')  # Redirect to the list of teams after deletion
    
    # Team creation view
    @login_required
    @role_required(allowed_roles=['leader'])
    def create_team(request):
        if request.method == 'POST':
            form = TeamForm(request.POST)
            if form.is_valid():
                team = form.save()
                member_ids = request.POST.getlist('members')
                for user_id in member_ids:
                    TeamMembership.objects.create(team=team, user_id=user_id)
                return redirect('teams')
        else:
            form = TeamForm()
        return render(request, 'team/create_team.html', {'form': form})

    # AJAX search view for users
    @login_required
    def search_users(request):
        query = request.GET.get('q', '')
        users = User.objects.filter(username__icontains=query)
        results = [{'id': user.id, 'username': user.username} for user in users]
        return JsonResponse(results, safe=False)

class CageClass:
    @login_required
    def all_cages(request):
        cages = Cage.objects.all()
        cage_data = []

        for cage in cages:
            # Filter for mice currently in the cage (i.e., with no end_date)
            current_mice = CageHistory.objects.filter(cage_id=cage, end_date__isnull=True)
            cage_data.append({
                'cage': cage,
                'current_mice': [history.mouse_id for history in current_mice]
            })

        context = {
            'cage_data': cage_data,
        }
        return render(request, 'cage/all_cages.html', context)
    
    @login_required
    #@role_required(allowed_roles=['leader'])
    def add_mouse_to_cage(request, cage_id):
        """Add a mouse to a cage."""
        cage = get_object_or_404(Cage, cage_id=cage_id)

        if request.method == 'POST':
            # Get the mouse ID from the form submission
            mouse_id = request.POST.get('mouse_id')

            if not mouse_id:
                return JsonResponse({'success': False, 'message': 'Mouse ID is required.'}, status=400)

            try:
                # Retrieve the mouse object using the mouse ID
                mouse = Mouse.objects.get(mouse_id=mouse_id)
            except Mouse.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Mouse not found.'}, status=404)

            # Check if the mouse is already in a cage
            current_cage_history = CageHistory.objects.filter(mouse_id=mouse.mouse_id, end_date__isnull=True).first()

            if current_cage_history:
                # Create a transfer request if the mouse is already in a cage
                TransferRequest.objects.create(
                    requester=request.user,
                    mouse=mouse,
                    source_cage=current_cage_history.cage_id,
                    destination_cage=cage,
                    status='pending',
                    request_date=timezone.now(),
                )
                return JsonResponse({'success': True, 'message': 'Transfer request created successfully!'})

            # Mouse is not currently in a cage; add it to the new cage
            CageHistory.objects.create(cage_id=cage, mouse_id=mouse, start_date=timezone.now(), end_date=None)
            return JsonResponse({'success': True, 'message': 'Mouse added to cage successfully!'})

        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)
    
    #@login_required
    #def fetch_available_mice(request):
    #    if request.method == 'GET' and request.headers.get("x-requested-with") == "XMLHttpRequest":  # Check if it's an AJAX request
    #        available_mice = Mouse.objects.exclude(cagehistory__end_date__isnull=False, cagehistory__cage_id=cage.cage_id)
    #        mice_data = [{"mouse_id": mouse.mouse_id, "name": f"Mouse {mouse.mouse_id}"} for mouse in available_mice]
    #        return JsonResponse({"success": True, "available_mice": mice_data})
    #    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)
    
    @login_required
    def fetch_available_mice(request):
        if request.method == 'GET' and request.headers.get("x-requested-with") == "XMLHttpRequest":  # Check if it's an AJAX request
            cage_id = request.GET.get('cage_id')  # Retrieve the cage ID from the query parameters
            if not cage_id:
                return JsonResponse({"success": False, "message": "Cage ID is required."}, status=400)

            try:
                # Ensure the cage exists
                cage = Cage.objects.get(cage_id=cage_id)
            except Cage.DoesNotExist:
                return JsonResponse({"success": False, "message": "Cage not found."}, status=404)

            # Exclude mice with an active cage history in any cage or already in the specified cage
            """available_mice = Mouse.objects.filter(
                ~Q(cagehistory__end_date__isnull=True) | Q(cagehistory__isnull=True)
            )"""
            available_mice = Mouse.objects.exclude(
                cagehistory__cage_id=cage_id
            ).exclude(
                Q(transfer_requests__status="pending")
            )

            # Prepare the response data
            mice_data = [{"mouse_id": mouse.mouse_id, "name": f"Mouse {mouse.mouse_id}"} for mouse in available_mice]
            return JsonResponse({"success": True, "available_mice": mice_data})

        return JsonResponse({"success": False, "message": "Invalid request"}, status=400)

    @login_required
    @role_required(allowed_roles=['leader'])
    def remove_mouse_from_cage(request, cage_id, mouse_id):
        """Remove a mouse from a cage."""
        cage = get_object_or_404(Cage, cage_id=cage_id)
        mouse = get_object_or_404(Mouse, id=mouse_id)

        # Find the CageHistory entry for the specific mouse in the cage
        cage_history_entry = get_object_or_404(CageHistory, cage_id=cage, mouse_id=mouse, end_date=None)

        # Set the end_date to now, effectively removing the mouse from the cage
        cage_history_entry.end_date = timezone.now()
        cage_history_entry.save()

        return redirect('cage_details', cage_id=cage.cage_id)

    @login_required
    def cage_details(request, cage_id):
        """View details for a specific cage."""
        cage = get_object_or_404(Cage, cage_id=cage_id)

        # Get all current mice in this cage
        current_mice = cage.cagehistory_set.filter(end_date=None).select_related('mouse_id')

        # Get the pending transfer requests for this cage (destination_cage = current cage)
        pending_transfers = TransferRequest.objects.filter(destination_cage=cage, status='pending')

        context = {
            'cage': cage,
            'current_mice': current_mice,
            'pending_transfers': pending_transfers,
        }
        return render(request, 'cage/cage_details.html', context)
    
    # Cage creation view
    @login_required
    @role_required(allowed_roles=['leader'])
    def create_cage(request):
        if request.method == 'POST':
            form = CageForm(request.POST)
            if form.is_valid():
                cage = form.save()  # Save the new cage
                mouse_ids = request.POST.getlist('mice')  # Get selected mouse IDs

                for mouse_id in mouse_ids:
                    mouse = Mouse.objects.get(id=mouse_id)
                    
                    # Check if the mouse is already in a different cage
                    current_cage_history = CageHistory.objects.filter(mouse_id=mouse, end_date__isnull=True).first()
                    
                    if current_cage_history:
                        # Mouse is already in a cage - create a transfer request
                        TransferRequest.objects.create(
                            requester=request.user,
                            mouse=mouse,
                            source_cage=current_cage_history.cage_id,
                            destination_cage=cage,
                            status='pending',
                            request_date=timezone.now(),
                        )
                    else:
                        # Mouse is not in any cage, so add it directly
                        CageHistory.objects.create(
                            cage_id=cage,
                            mouse_id=mouse,
                            start_date=timezone.now(),
                            end_date=None
                        )

                return redirect('cages')  # Redirect to the cage list
        else:
            form = CageForm()
        
        return render(request, 'cage/create_cage.html', {'form': form})
    
    # @login_required
    # def search_mice(request):
    #     query = request.GET.get('q', '').strip()  # Get and sanitize query
    #     mice = Mouse.objects.filter(
    #         Q(mouse_id__icontains=query) |  # Search by partial match on mouse ID
    #         Q(state__icontains=query) |  # Search by state (e.g., "alive", "deceased")
    #         Q(sex__icontains=query) |  # Search by sex ("M" or "F")
    #         Q(strain__name__icontains=query)  # Search by strain name (requires strain.name field)
    #     )
        
    #     # Return structured data with relevant details
    #     results = [
    #         {
    #             'id': mouse.mouse_id,
    #             'strain': mouse.strain.name if mouse.strain else "Unknown",
    #             'dob': mouse.dob.strftime('%Y-%m-%d'),
    #             'sex': dict(Mouse.SEX_CHOICES).get(mouse.sex, "Unknown"),  # Resolve choice display name
    #             'state': dict(Mouse.STATE_CHOICES).get(mouse.state, "Unknown")  # Resolve state display name
    #         } for mouse in mice
    #     ]
        
    #     return JsonResponse(results, safe=False)
    
    @login_required
    def search_mice(request):
        query = request.GET.get('q', '')
        mice = Mouse.objects.filter(state__icontains=query)
        results = [{'mouse_id': mouse.mouse_id, 'sex': mouse.sex} for mouse in mice]
        return JsonResponse(results, safe=False)
    
class AllRequestsClass:
    @login_required
    # @role_required(allowed_roles=["breeder"])
    def all_requests(request):
        # Filter requests based on user role
        if request.user.role == 'breeder':
            # If the user is a breeder, show all requests
            transfers = TransferRequest.objects.all().exclude(status="completed").exclude(status="rejected")
            breedings = BreedingRequest.objects.all().exclude(status="completed").exclude(status="rejected")
            cullings = CullingRequest.objects.all().exclude(status="completed").exclude(status="rejected")
            completed_transfers = TransferRequest.objects.all().exclude(status="pending").exclude(status="approved")
            completed_breedings = BreedingRequest.objects.all().exclude(status="pending").exclude(status="approved")
            completed_cullings = CullingRequest.objects.all().exclude(status="pending").exclude(status="approved")
        else:
            # If the user is not a breeder, show only their requests
            transfers = TransferRequest.objects.filter(requester=request.user).exclude(status="completed").exclude(status="rejected")
            breedings = BreedingRequest.objects.filter(requester=request.user).exclude(status="completed").exclude(status="rejected")
            cullings = CullingRequest.objects.filter(requester=request.user).exclude(status="completed").exclude(status="rejected")
            completed_transfers = TransferRequest.objects.filter(requester=request.user).exclude(status="pending").exclude(status="approved")
            completed_breedings = BreedingRequest.objects.filter(requester=request.user).exclude(status="pending").exclude(status="approved")
            completed_cullings = CullingRequest.objects.filter(requester=request.user).exclude(status="pending").exclude(status="approved")
        
        context = {
            "current_transfers": transfers,
            "current_breedings": breedings,
            "current_cullings": cullings,
            "completed_transfers": completed_transfers,
            "completed_breedings": completed_breedings,
            "completed_cullings": completed_cullings,
        }

        return render(request, 'requests/all_requests.html', context)


class TransferRequestClass:
    @login_required
    @role_required(allowed_roles=['leader'])
    def create_transfer_request(request):
        if request.method == 'POST':
            form = TransferRequestForm(request.POST)
            if form.is_valid():
                transfer_request = form.save(commit=False)
                transfer_request.requester = request.user  # Set the requester to the current user
                transfer_request.save()
                return redirect('all_requests')  # Redirect after successful submission
        else:
            form = TransferRequestForm()

        return render(request, 'requests/create_transfer_request.html', {'form': form})
    
    @login_required
    def cancel_transfer_request(request, transfer_id):
        transfer_request = get_object_or_404(TransferRequest, id=transfer_id)
    
        # Check if the request is pending
        if transfer_request.status == 'pending':
            transfer_request.delete()
            # Optionally, add a success message
            messages.success(request, "Transfer request has been canceled.")
        else:
            # If the request is not pending, you might want to show an error
            messages.error(request, "Only pending requests can be canceled.")

        return redirect('all_requests')
    
    @login_required
    @role_required(allowed_roles=['breeder'])
    def approve_transfer_request(request, transfer_id):
        """Approve a transfer request and move the mouse to the new cage."""
        transfer_request = get_object_or_404(TransferRequest, id=transfer_id)

        if transfer_request.status == 'pending':
            # Complete the transfer: close current CageHistory and create a new one
            current_cage_history = CageHistory.objects.filter(
                mouse_id=transfer_request.mouse,
                cage_id=transfer_request.source_cage,
                end_date__isnull=True
            ).first()

            if current_cage_history:
                current_cage_history.end_date = timezone.now()
                current_cage_history.save()

            # Start a new CageHistory for the destination cage
            CageHistory.objects.create(
                cage_id=transfer_request.destination_cage,
                mouse_id=transfer_request.mouse,
                start_date=timezone.now(),
                end_date=None
            )

            # Mark the transfer request as completed
            transfer_request.status = 'completed'
            transfer_request.save()

        return redirect('all_requests')  # Redirect to a list of all requests
    
    @login_required
    @role_required(allowed_roles=['breeder'])
    def reject_transfer_request(request, transfer_id):
        """Reject a transfer request, leaving the mouse in its original cage."""
        transfer_request = get_object_or_404(TransferRequest, id=transfer_id)

        if transfer_request.status == 'pending':
            transfer_request.status = 'rejected'
            transfer_request.save()

        return redirect('all_requests')
    
    def get_transfer_data(request):
        if request.method == 'GET':
            mouse_id = request.GET.get('mouse_id')
            current_cage_id = None
            destination_cages = []

            if mouse_id:
                # Get the current cage for the selected mouse
                current_cage_history = CageHistory.objects.filter(
                    mouse_id=mouse_id,
                    end_date__isnull=True
                ).first()

                if current_cage_history:
                    current_cage_id = current_cage_history.cage_id.cage_id
                    # Get all cages except the current cage for destination
                    destination_cages = Cage.objects.exclude(cage_id=current_cage_id).values('cage_id', 'cage_number', 'cage_type')

            return JsonResponse({
                'current_cage_id': current_cage_id,
                'destination_cages': list(destination_cages)
            })
    
class BreedingRequestClass:
    @login_required
    @role_required(allowed_roles=['leader'])
    def create_breeding_request(request):
        if request.method == 'POST':
            form = BreedingRequestForm(request.POST)
            if form.is_valid():
                breeding_request = form.save(commit=False)
                breeding_request.requester = request.user  # Set the requester to the current user
                breeding_request.save()
                return redirect('all_requests')  # Redirect after successful submission
        else:
            form = BreedingRequestForm()
        
        return render(request, 'requests/create_breeding_request.html', {'form': form})
    
    @login_required
    def cancel_breeding_request(request, breeding_id):
        breeding_request = get_object_or_404(BreedingRequest, id=breeding_id)
    
        # Check if the request is pending
        if breeding_request.status == 'pending':
            breeding_request.delete()
            # Optionally, add a success message
            messages.success(request, "Breeding request has been canceled.")
        else:
            # If the request is not pending, you might want to show an error
            messages.error(request, "Only pending requests can be canceled.")

        return redirect('all_requests')
    
    @login_required
    @role_required(allowed_roles=['breeder'])
    def approve_breeding_request(request, breeding_id):
        """Approve a breeding request and move both mice to the breeding cage."""
        breeding_request = get_object_or_404(BreedingRequest, id=breeding_id)

        if breeding_request.status == 'pending':
            # Check if both mice are currently in different cages and available for breeding
            for mouse in [breeding_request.male_mouse, breeding_request.female_mouse]:
                current_cage_history = CageHistory.objects.filter(
                    mouse_id=mouse,
                    end_date__isnull=True
                ).first()

                if current_cage_history:
                    # Set the end date of the current cage history entry to mark the mouse leaving
                    current_cage_history.end_date = timezone.now()
                    current_cage_history.save()

            # Start new CageHistory entries for both mice in the breeding cage
            CageHistory.objects.create(
                cage_id=breeding_request.cage,
                mouse_id=breeding_request.male_mouse,
                start_date=timezone.now(),
                end_date=None
            )

            CageHistory.objects.create(
                cage_id=breeding_request.cage,
                mouse_id=breeding_request.female_mouse,
                start_date=timezone.now(),
                end_date=None
            )

            # Update the status of the mice to 'breeding'
            breeding_request.male_mouse.state = 'breeding'
            breeding_request.female_mouse.state = 'breeding'
            breeding_request.male_mouse.save()
            breeding_request.female_mouse.save()

            # Mark the breeding request as completed
            breeding_request.status = 'completed'
            breeding_request.save()

        return redirect('all_requests')  # Redirect to a list of all requests

    @login_required
    @role_required(allowed_roles=['breeder'])
    def reject_breeding_request(request, breeding_id):
        """Reject a breeding request, leaving both mice in their original cages."""
        breeding_request = get_object_or_404(BreedingRequest, id=breeding_id)

        if breeding_request.status == 'pending':
            breeding_request.status = 'rejected'
            breeding_request.save()

        return redirect('all_requests')

class CullingRequestClass:
    @login_required
    @role_required(allowed_roles=['leader'])
    def create_culling_request(request):
        if request.method == 'POST':
            form = CullingRequestForm(request.POST)
            if form.is_valid():
                culling_request = form.save(commit=False)
                culling_request.requester = request.user  # Set the requester to the current user
                culling_request.save()
                return redirect('all_requests')  # Redirect after successful submission
        else:
            form = CullingRequestForm()
        
        return render(request, 'requests/create_culling_request.html', {'form': form})
    
    @login_required
    def cancel_culling_request(request, culling_id):
        culling_request = get_object_or_404(CullingRequest, id=culling_id)
    
        # Check if the request is pending
        if culling_request.status == 'pending':
            culling_request.delete()
            # Optionally, add a success message
            messages.success(request, "Culling request has been canceled.")
        else:
            # If the request is not pending, you might want to show an error
            messages.error(request, "Only pending requests can be canceled.")

        return redirect('all_requests')
    
    @login_required
    @role_required(allowed_roles=['breeder'])
    def approve_culling_request(request, culling_id):
        """Approve a culling request and mark the mouse as deceased."""
        culling_request = get_object_or_404(CullingRequest, id=culling_id)

        if culling_request.status == 'pending':
            # Retrieve the current cage history of the mouse, if it exists
            current_cage_history = CageHistory.objects.filter(
                mouse_id=culling_request.mouse,
                end_date__isnull=True
            ).first()

            if current_cage_history:
                # End the current cage history, as the mouse is being culled
                current_cage_history.end_date = timezone.now()
                current_cage_history.save()

            # Mark the mouse as deceased and set the cull date
            culling_request.mouse.state = 'deceased'
            culling_request.mouse.cull_date = timezone.now()
            culling_request.mouse.save()

            # Mark the culling request as completed
            culling_request.status = 'completed'
            culling_request.save()

        return redirect('all_requests')  # Redirect to a list of all requests

    @login_required
    @role_required(allowed_roles=['breeder'])
    def reject_culling_request(request, culling_id):
        """Reject a culling request, leaving the mouse in its original cage."""
        culling_request = get_object_or_404(CullingRequest, id=culling_id)

        if culling_request.status == 'pending':
            # Set the culling request status to rejected
            culling_request.status = 'rejected'
            culling_request.save()

        return redirect('all_requests')