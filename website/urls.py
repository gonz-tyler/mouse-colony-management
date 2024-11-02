from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    # path('admin/', admin.site.urls),
    path('legal/terms-of-service/', views.terms_of_service, name='terms_of_service'), # legal
    path('legal/privacy-policy/', views.privacy_policy, name='privacy_policy'), # legal
    path('', views.home_view, name='index'),  # Index page
    path('login/', auth_views.LoginView.as_view(), name='login'),  # Login page
    path('register/', views.register, name='register'), # Register page
    path('logout/', views.logout_user, name="logout_user"),
    path('genetic-tree/<int:mouse_id>/', views.genetic_tree, name='genetic_tree'), # Genetic Tree page

    # --- mice ---
    path('mice/<int:mouse_id>/', views.MouseClass.view_mouse, name='view_mouse'),
    path('mice/add/', views.MouseClass.add_mouse, name='add_mouse'),
    path('mice/update/<int:mouse_id>/', views.MouseClass.MouseUpdateView.as_view(), name='update_mouse'),
    path('mice/delete/<int:mouse_id>/', views.MouseClass.delete_mouse, name='delete_mouse'),

    # --- team ---
    path('create-team/', views.TeamClass.create_team, name='create_team'),
    path('search-users/', views.TeamClass.search_users, name='search_users'),
    path('teams/', views.TeamClass.all_teams, name='teams'),  # Display all teams
    path('team/<str:team_name>/', views.TeamClass.team_details, name='team_details'),
    path('team/<str:team_name>/join/', views.TeamClass.join_team, name='join_team'),
    path('team/<str:team_name>/leave/', views.TeamClass.leave_team, name='leave_team'),
    path('team/<str:team_name>/delete/', views.TeamClass.delete_team, name='delete_team'),

]
