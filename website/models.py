from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime as dt
import os
from cloudinary.models import CloudinaryField
import cloudinary
import cloudinary.api
import logging

# Define logger
logger = logging.getLogger(__name__)


    
# ---------- Cage Model ----------
class Cage(models.Model):
    cage_id = models.AutoField(primary_key=True)
    cage_number = models.CharField(max_length=10, unique=True)
    cage_type = models.CharField(max_length=25)
    location = models.CharField(max_length=25)

    def __str__(self):
        return self.cage_number
    
# ---------- Cage History Model ----------
class CageHistory(models.Model):
    cage_id = models.ForeignKey(Cage, on_delete=models.CASCADE)
    mouse_id = models.ForeignKey('Mouse', on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    def clean(self):
        # Ensure end_date is after start_date
        if self.end_date is not None and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date.')

    def save(self, *args, **kwargs):
        # Call clean method before saving
        self.clean()
        super().save(*args, **kwargs)

# ---------- User Model ----------
class User(AbstractUser):
    ROLE_CHOICES = [
        ('leader', 'Leader'),
        ('staff', 'Staff'),
        ('new_staff', 'New Staff'),
        ('breeder', 'Breeder'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='new_staff')

    email = models.EmailField(unique=True)  # Add unique constraint to email

    profile_picture = CloudinaryField("image", blank=True, null=True)

    # Enforce email validation
    def clean(self):
        super().clean()
        if self.email and not self.email.endswith('@abdn.ac.uk'):
            raise ValidationError(_('Email must be an @abdn.ac.uk address.'))

    def save(self, *args, **kwargs):
        self.full_clean()  # Calls the clean method before saving

        # Check if a profile picture is already set and if it is a new picture
        if self.pk:
            # If there's an old profile picture, delete it
            old_picture = User.objects.get(pk=self.pk).profile_picture
            if old_picture and old_picture != self.profile_picture:
                # Delete the old profile picture file if it exists on Cloudinary
                if old_picture and old_picture.public_id:
                    cloudinary.api.delete_resources([old_picture.public_id])

        # Save the new profile picture
        super().save(*args, **kwargs)

# ---------- Team Model ----------
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
# ---------- Team Membership ----------
class TeamMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    
    class Meta:
        unique_together = ("user", "team")

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.user.role})"

# ---------- Weight Model ----------
class Weight(models.Model):
    weight_id = models.AutoField(primary_key=True)
    mouse = models.ForeignKey('Mouse', on_delete=models.CASCADE)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    measured_at = models.DateTimeField(null=True, blank=True)

# ---------- Mouse Model ----------
class Mouse(models.Model):
    SEX_CHOICES = [('M', 'Male'), ('F', 'Female')]
    CLIPPED_CHOICES = [
        ('TL', 'Top Left'),
        ('TR', 'Top Right'),
        ('BL', 'Bottom Left'),
        ('BR', 'Bottom Right'),
    ]
    STATE_CHOICES = [('alive', 'Alive'), ('breeding', 'Breeding'), ('to_be_culled', 'To Be Culled'), ('deceased', 'Deceased')]
    GENOTYPE_CHOICES = [('wt', 'Wild type'), ('ht', 'Heterozygous'), ('ko', 'Knock out'), ('na', 'N/A')]


    mouse_id = models.AutoField(primary_key=True)
    strain = models.ForeignKey('Strain', on_delete=models.CASCADE)
    tube_id = models.IntegerField()
    dob = models.DateField()
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='M', blank=False, null=False)
    father = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='father_of', limit_choices_to={'sex': 'M'})
    mother = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='mother_of', limit_choices_to={'sex': 'F'})
    earmark = models.CharField(max_length=20, choices=CLIPPED_CHOICES, blank=True, null=True)
    # earmark = models.JSONField(default=list, blank=True, null=True)
    clipped_date = models.DateField(null=True, blank=True)
    state = models.CharField(max_length=12, choices=STATE_CHOICES, default='alive', blank=False)
    cull_date = models.DateTimeField(null=True, blank=True)
    weaned = models.BooleanField(default=False)
    weaned_date = models.DateField(null=True, blank=True)
    genotype = models.CharField(max_length=20, choices=GENOTYPE_CHOICES, default='na', blank=False)
    # change mouse to mousekeeper table
    #mouse_keeper = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='kept_mice')

    def get_earmark_display(self):
        """Return a readable string of earmark choices."""
        # Map the list of choices to their corresponding labels in CLIPPED_CHOICES
        choice_dict = dict(self.CLIPPED_CHOICES)
        return ''.join(choice_dict.get(choice, choice) for choice in self.earmark)

    def get_earmark_choices(self):
        """Return the list of earmark choices directly."""
        return self.earmark if self.earmark else []
    
    def get_genotype_display(self):
        """Return a readable string of genotype choices."""
        # Map the list of choices to their corresponding labels in GENOTYPE_CHOICES
        choice_dict = dict(self.GENOTYPE_CHOICES)
        return ''.join(choice_dict.get(choice, choice) for choice in self.genotype)

    def set_earmark_choices(self, choices):
        """Set the list of earmark choices."""
        if isinstance(choices, list):
            self.earmark = choices
        else:
            raise ValueError("Choices must be a list of strings.")

    class Meta:
        unique_together = ('strain', 'tube_id')

    def __str__(self):
        return f"Mouse {self.mouse_id} - {self.strain} - Tube {self.tube_id}"
    
    def get_ancestors(self):
        ancestors = []
        if self.mother:
            ancestors.append(self.mother)
            ancestors.extend(self.mother.get_ancestors())
        if self.father:
            ancestors.append(self.father)
            ancestors.extend(self.father.get_ancestors())
        return ancestors
    
    def get_parents(self):
        parents = []
        if self.mother:
            parents.append(self.mother)
        if self.father:
            parents.append(self.father)
        return parents

    def get_descendants(self):
        descendants = list(self.mother_of.all()) + list(self.father_of.all())
        for child in descendants:
            descendants.extend(child.get_descendants())
        return descendants
    
    def is_kept_by_user(self, user):
        return MouseKeeper.objects.filter(mouse=self, user=user).exists()

    def is_kept_by_team(self, team):
        return MouseKeeper.objects.filter(mouse=self, team=team).exists()

    @classmethod
    def mice_managed_by_user(cls, user):
        # Start with an empty queryset
        mice = cls.objects.none()

        # Retrieve all mice directly kept by the user if they are a MouseKeeper
        if MouseKeeper.objects.filter(user=user).exists():
            direct_mice = cls.objects.filter(mousekeeper__user=user)
        else:
            direct_mice = cls.objects.none()

        # Retrieve all team IDs the user is part of, if any
        team_ids = TeamMembership.objects.filter(user=user).values_list('team', flat=True)
        
        # Retrieve mice associated with these teams, if any
        if team_ids:
            team_mice = cls.objects.filter(mousekeeper__team__in=team_ids)
        else:
            team_mice = cls.objects.none()

        # Combine direct mice and team-associated mice, ensuring no duplicates
        mice = (direct_mice | team_mice).distinct()

        return mice

# ---------- Mouse Keeper Model ----------
class MouseKeeper(models.Model):
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('mouse', 'user', 'team')

    def clean(self):
        # Ensure only one of user or team is set
        if self.user and self.team:
            raise ValidationError("Specify only one of user or team as the keeper.")
        if not (self.user or self.team):
            raise ValidationError("Specify at least one keeper (user or team).")
        super().clean()

    def __str__(self):
        return f"Mouse {self.mouse.mouse_id} - Keeper {self.user or self.team}"

# ---------- Project Model ----------
class Project(models.Model):
    project_id = models.BigAutoField(primary_key=True)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(blank=True, null=True)

# ---------- Project Mouse Model ----------
class ProjectMouse(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    mouse_id = models.ForeignKey(Mouse, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('project_id', 'mouse_id')

# ---------- Project User Model ----------
class ProjectUser(models.Model):
    project_id = models.ForeignKey(Project, on_delete=models.CASCADE)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('project_id', 'user_id')

# # ---------- Request Model ----------
# class Request(models.Model):
#     REQUEST_TYPES = [
#         ('breed', 'Breeding Request'),
#         ('cull', 'Culling Request'),
#         # ('end_breed', 'End Breeding Request'),
#     ]
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('approved', 'Approved'),
#         ('rejected', 'Rejected'),
#         ('completed', 'Completed'),
#     ]
#     request_id = models.AutoField(primary_key=True)
#     requester = models.ForeignKey(User, on_delete=models.CASCADE)
#     mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, related_name='primary_mouse_requests')
#     second_mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, null=True, blank=True, related_name='secondary_mouse_requests', help_text="For breeding requests, select a second mouse of the opposite sex.")
#     cage = models.ForeignKey(Cage, on_delete=models.CASCADE, null=True, blank=True, help_text="Required for breeding requests.")
#     request_type = models.CharField(max_length=10, choices=REQUEST_TYPES)
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
#     submitted_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     comments = models.TextField(blank=True, null=True)

#     def clean(self):
#         """Custom validation for the request model."""
#         # Ensure second_mouse is provided only for breeding requests
#         if self.request_type == 'breed':
#             if not self.second_mouse:
#                 raise ValidationError("Breeding requests must specify a second mouse.")
#             # Ensure the two mice are of opposite sex
#             if self.mouse.sex == self.second_mouse.sex:
#                 raise ValidationError("For breeding requests, the two mice must be of opposite sexes.")
#             # Ensure a cage is provided for breeding requests
#             if not self.cage:
#                 raise ValidationError("A cage must be specified for breeding requests.")
#         elif self.request_type == 'cull':
#             if self.second_mouse:
#                 raise ValidationError("Culling requests should not have a second mouse.")
#             # Ensure that cage is not set for non-breeding requests
#             if self.cage:
#                 raise ValidationError(f"A cage should not be specified for {self.request_type} requests.")

#         super().clean()

#     def __str__(self):
#         if self.request_type == 'breed':
#             return f"Breeding Request: {self.mouse.mouse_id} with {self.second_mouse.mouse_id} by {self.requester.username}"
#         return f"{self.request_type} Request by {self.requester.username} for Mouse {self.mouse.mouse_id}"

#     def approve(self):
#         self.status = 'approved'
#         self.save()

#     def reject(self):
#         self.status = 'rejected'
#         self.save()

#     def complete(self):
#         self.status = 'completed'
#         self.save()

#         # Handle culling request completion
#         if self.request_type == 'cull':
#             self.mouse.state = 'deceased'
#             self.mouse.cull_date = dt.datetime.now()
#             self.mouse.save()

#         # Handle breeding request completion
#         if self.request_type == 'breed':
#             self.mouse.state = 'breeding'  # Update first mouse to breeding state
#             self.second_mouse.state = 'breeding'  # Update second mouse to breeding state
#             self.mouse.save()
#             self.second_mouse.save()

#             # Create a new Breed instance
#             Breed.objects.create(
#                 male=self.mouse,
#                 female=self.second_mouse,
#                 cage=self.cage,
#             )

#         # # Handle end breeding request completion
#         # if self.request_type == 'end_breed':
#         #     self.mouse.state = 'alive'  # Update first mouse to alive state
#         #     self.second_mouse.state = 'alive'  # Update second mouse to alive state
#         #     self.mouse.save()
#         #     self.second_mouse.save()

# ---------- Base Request Model ----------
class BaseRequest(models.Model):
    STATUS_CHOICES = [('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')]
    requester = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    

    class Meta:
        abstract = True
    
    def is_completed(self):
        return self.status == 'completed'
    
    def is_rejected(self):
        return self.status == 'rejected'
    
    def is_approved(self):
        return self.status == 'approved'
    
    def is_pending(self):
        return self.status == 'pending'
    
    def get_request_type(self):
        return self.__class__.__name__.replace('Request', '').lower()
    
    def get_absolute_url(self):
        return f"/requests/{self.get_request_type()}/{self.id}/"
    
    def notify_status_change(self):
        """Notify the requester about the status change."""
        if self.status == 'approved':
            msg = f"Your {self.get_request_type()} request has been approved."
        elif self.status == 'rejected':
            msg = f"Your {self.get_request_type()} request was rejected: {self.comments}"
        else:
            return
        
        if not self.requester:
            logger.error(f"Requester for {self.get_request_type()} request ID {self.id} is None.")
            return
        
        print(f"Sending notification to {self.requester.username}: {msg}")

        Notification.objects.create(
            recipient=self.requester,
            message=msg,
            request_type=self.get_request_type(),
            request_id=self.id,
        )

# ---------- Breeding Request Model ----------
class BreedingRequest(BaseRequest):
    male_mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, related_name='breeding_male_requests', limit_choices_to={'sex': 'M'})
    female_mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, related_name='breeding_female_requests', limit_choices_to={'sex': 'F'})
    cage = models.ForeignKey(Cage, on_delete=models.CASCADE, help_text="Cage for breeding")
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='breeding_requests', null=True, blank=True)

    def clean(self):
        if self.male_mouse.sex != 'M' or self.female_mouse.sex != 'F':
            raise ValidationError("For breeding, select one male and one female mouse.")
        if not self.cage:
            raise ValidationError("A cage must be specified for breeding requests.")
        super().clean()

    def approve(self, approver):
        self.status = 'approved'
        self.approval_date = dt.datetime.now()
        self.save()
        # Change mice states and create a Breed instance
        self.male_mouse.state = 'breeding'
        self.female_mouse.state = 'breeding'
        self.male_mouse.save()
        self.female_mouse.save()
        Breed.objects.create(male=self.male_mouse, female=self.female_mouse, cage=self.cage)

    def complete(self):
        self.status = 'completed'
        self.save()
        # Additional logic on completion (optional)
    
    def reject(self):
        self.status = 'rejected'
        self.save()

# ---------- Culling Request Model ----------
class CullingRequest(BaseRequest):
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, related_name='culling_requests')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='culling_requests', null=True, blank=True)

    def complete(self):
        self.status = 'completed'
        self.mouse.state = 'deceased'
        self.mouse.cull_date = dt.datetime.now()
        self.mouse.save()
        self.save()

    def approve(self, approver):
        self.status = 'approved'
        self.approval_date = dt.datetime.now()
        self.save()

    def reject(self):
        self.status = 'rejected'
        self.save()

# ---------- Transfer Request Model ----------
class TransferRequest(BaseRequest):
    mouse = models.ForeignKey(Mouse, on_delete=models.CASCADE, related_name='transfer_requests')
    source_cage = models.ForeignKey(Cage, on_delete=models.SET_NULL, null=True, related_name='source_transfers')
    destination_cage = models.ForeignKey(Cage, on_delete=models.CASCADE, related_name='destination_transfers')
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transfer_requests', null=True, blank=True)

    def clean(self):
        # Ensure that destination_cage is set before checking
        if self.destination_cage is None:
            raise ValidationError({'destination_cage': 'Destination cage cannot be empty.'})
        
        # Custom validation to ensure source_cage and destination_cage are different
        if self.source_cage == self.destination_cage:
            raise ValidationError({'destination_cage': 'Destination cage cannot be the same as the source cage.'})

    def approve(self, approver):
        self.status = 'approved'
        self.approval_date = dt.datetime.now()
        self.save()
        # Update mouse's cage history
        CageHistory.objects.filter(mouse_id=self.mouse, end_date__isnull=True).update(end_date=dt.datetime.now())
        CageHistory.objects.create(cage_id=self.destination_cage, mouse_id=self.mouse, start_date=dt.datetime.now())
    
    def reject(self):
        self.status = 'rejected'
        self.save()

# ---------- Breed Model ----------
class Breed(models.Model):
    breed_id = models.AutoField(primary_key=True)
    male = models.ForeignKey(Mouse, on_delete=models.CASCADE, limit_choices_to={'sex': 'M'}, related_name='male_breeds')
    female = models.ForeignKey(Mouse, on_delete=models.CASCADE, limit_choices_to={'sex': 'F'}, related_name='female_breeds')
    cage = models.ForeignKey(Cage, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)

    def end_breeding(self):
        """Set the breeding as finished and update mouse states."""
        self.end_date = dt.datetime.now()
        self.male.state = 'alive'  # Adjusted from 'active' to a valid state
        self.female.state = 'alive'  # Adjusted from 'active' to a valid state
        self.male.save()
        self.female.save()
        self.save()
    
    def __str__(self):
        return f"Breeding {self.male.mouse_id} x {self.female.mouse_id}"

# ---------- Strain Model ----------
class Strain(models.Model):
    name = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.name

# ---------- Notification Model ----------
class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    request_type = models.CharField(max_length=20, null=True, blank=True, help_text="Type of request associated with the notification.")
    request_id = models.IntegerField(null=True, blank=True, help_text="ID of the associated request.")

    def __str__(self):
        return f"Notification for {self.recipient.username} - {self.message[:20]}..."