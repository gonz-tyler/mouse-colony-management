from django.contrib import admin
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static
from .forms import UserPasswordResetForm
urlpatterns = [
    # path('admin/', admin.site.urls),
    path('legal/terms-of-service/', views.terms_of_service, name='terms_of_service'), # legal
    path('legal/privacy-policy/', views.privacy_policy, name='privacy_policy'), # legal
    path('download-database/', views.download_database_csv, name='download_database_csv'),
    path('', views.home_view, name='index'),  # Index page
    path('login/', auth_views.LoginView.as_view(), name='login'),  # Login page
    path('register/', views.register, name='register'), # Register page
    path('logout/', views.logout_user, name="logout_user"),
    path('delete-account/', views.delete_account, name="delete_account"),
    path('change-password/', auth_views.PasswordChangeView.as_view(template_name='registration/change_password.html', success_url=reverse_lazy('index')), name='change_password'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.user_profile, name="user_profile"),
    path('notifications/<str:username>/', views.notifications, name="notifications"), # Notifications page
    path('notifications/mark-as-read/<str:username>/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'), # Mark notification as read
    path('notifications/delete/<int:notification_id>/', views.delete_notification, name='delete_notification'), # Delete notification
    path('genetic-tree/<int:mouse_id>/', views.genetic_tree, name='genetic_tree'), # Genetic Tree page
    # User Management
    path('manage-users/', views.manage_users, name='manage_users'),
    path('update-user-role/<int:user_id>/', views.update_user_role, name='update_user_role'),

    # Password reset URLs
    # path('password-reset/', views.password_reset, name='password_reset'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accounts/password_reset_form.html', html_email_template_name='accounts/password_reset_email.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),

    # --- mice ---
    path('mice/<int:mouse_id>/', views.MouseClass.view_mouse, name='view_mouse'),
    path('mice/add/', views.MouseClass.add_mouse, name='add_mouse'),
    path('mice/update/<int:mouse_id>/', views.MouseClass.MouseUpdateView.as_view(), name='update_mouse'),
    path('mice/delete/<int:mouse_id>/', views.MouseClass.delete_mouse, name='delete_mouse'),

    # --- strain ---
    path('strain/add/', views.StrainClass.create_strain, name='create_strain'),

    # --- team ---
    path('team/create', views.TeamClass.create_team, name='create_team'),
    path('search-users/', views.TeamClass.search_users, name='search_users'),
    path('teams/', views.TeamClass.all_teams, name='teams'),  # Display all teams
    path('team/<str:team_name>/', views.TeamClass.team_details, name='team_details'),
    path('team/<str:team_name>/join/', views.TeamClass.join_team, name='join_team'),
    path('team/<str:team_name>/leave/', views.TeamClass.leave_team, name='leave_team'),
    path('team/<str:team_name>/delete/', views.TeamClass.delete_team, name='delete_team'),

    # --- cage ---
    path('cages/', views.CageClass.all_cages, name='cages'),
    path('cage/create', views.CageClass.create_cage, name='create_cage'),
    path('cage/<int:cage_id>/add_mouse_to_cage/', views.CageClass.add_mouse_to_cage, name='add_mouse_to_cage'),
    path('cage/available-mice/', views.CageClass.fetch_available_mice, name='fetch_available_mice'),
    path('search-mice/', views.CageClass.search_mice, name='search_mice'),
    path('cage/<int:cage_id>/', views.CageClass.cage_details, name='cage_details'),

    # --- request ---
    # transfer
    path('requests/', views.AllRequestsClass.all_requests, name="all_requests"),
    path('requests/create/transfer-request', views.TransferRequestClass.create_transfer_request, name="create_transfer_request"),
    path('requests/get-transfer-data/', views.TransferRequestClass.get_transfer_data, name='get_transfer_data'),
    path('requests/cancel-transfer/<int:transfer_id>', views.TransferRequestClass.cancel_transfer_request, name="cancel_transfer_request"),
    path('requests/approve-transfer/<int:transfer_id>/', views.TransferRequestClass.approve_transfer_request, name='approve_transfer'),
    path('requests/reject-transfer/<int:transfer_id>/', views.TransferRequestClass.reject_transfer_request, name='reject_transfer'),
    # breeding
    path('breedings/', views.BreedingsClass.all_breedings, name="all_breedings"),
    path('breedings/end-breeding/<int:breeding_id>/', views.BreedingsClass.end_breeding, name='end_breeding'),
    path('requests/create/breeding-request', views.BreedingRequestClass.create_breeding_request, name="create_breeding_request"),
    path('requests/cancel-breeding/<int:breeding_id>', views.BreedingRequestClass.cancel_breeding_request, name="cancel_breeding_request"),
    path('requests/approve-breeding/<int:breeding_id>/', views.BreedingRequestClass.approve_breeding_request, name='approve_breeding'),
    path('requests/reject-breeding/<int:breeding_id>/', views.BreedingRequestClass.reject_breeding_request, name='reject_breeding'),
    # culling
    path('requests/create/culling-request', views.CullingRequestClass.create_culling_request, name="create_culling_request"),
    path('requests/cancel-culling/<int:culling_id>', views.CullingRequestClass.cancel_culling_request, name="cancel_culling_request"),
    path('requests/approve-culling/<int:culling_id>/', views.CullingRequestClass.approve_culling_request, name='approve_culling'),
    path('requests/reject-culling/<int:culling_id>/', views.CullingRequestClass.reject_culling_request, name='reject_culling'),


]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
