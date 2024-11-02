from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from .decorators import role_required
from .models import *
from .forms import *

from django.views.generic.edit import UpdateView

# --- Messages ---
record_added = "Record has been added successfully."
record_deleted = "Record has been deleted successfully."
record_updated = "Record has been updated successfully."

# Legal Boiler-plate Views
def terms_of_service(request):
    return render(request, 'legal/terms-of-service.html')
def privacy_policy(request):
    return render(request, 'legal/privacy-policy.html')


@login_required
def home_view(request):
    # Fetch only the Mouse records that belong to the logged-in user
    mice = Mouse.mice_managed_by_user(request.user)
    return render(request, 'home.html', {'mice': mice})

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, "You have been logged out...")
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Log the user in after registration
            return redirect('index')  # Redirect to homepage
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

# Generate genetic tree
def genetic_tree(request, mouse_id):
    mouse = get_object_or_404(Mouse, mouse_id=mouse_id)
    ancestors = mouse.get_ancestors()
    descendants = mouse.get_descendants()

    context = {
        'mouse': mouse,
        'ancestors': ancestors,
        'descendants': descendants,
    }
    return render(request, 'genetictree.html', context)


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
                    MouseKeeper.objects.create(mouse=mouse, team=team, start_date=dt.datetime.now())
                else:
                    # Otherwise, connect the mouse to the logged-in user
                    MouseKeeper.objects.create(mouse=mouse, user=request.user, start_date=dt.datetime.now())

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


