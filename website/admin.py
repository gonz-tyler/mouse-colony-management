from django.contrib import admin
from django.contrib.auth.models import User as DefaultUser
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import *

# Register your custom User model with the default UserAdmin options
@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):
    # Specify the additional fields from your User model to be displayed in admin
    fieldsets = DefaultUserAdmin.fieldsets + (
        (None, {'fields': ('role',)}),
    )

admin.site.register(Weight)
admin.site.register(Cage)
admin.site.register(CageHistory)
admin.site.register(Team)
admin.site.register(TeamMembership)
admin.site.register(Mouse)
admin.site.register(MouseKeeper)
admin.site.register(BreedingRequest)
admin.site.register(TransferRequest)
admin.site.register(CullingRequest)
admin.site.register(Breed)
admin.site.register(Strain)
admin.site.register(Project)
admin.site.register(ProjectMouse)
admin.site.register(ProjectUser)
