from django.apps import AppConfig


class WebsiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'website'

    def ready(self):
        # Import your models and ensure groups are created
        from .models import Profile
        Profile.create_default_groups()