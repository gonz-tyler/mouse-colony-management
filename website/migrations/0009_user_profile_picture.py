# Generated by Django 5.1.2 on 2025-01-26 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0008_alter_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='profile_picture',
            field=models.ImageField(blank=True, null=True, upload_to='static/media/profile_pictures/'),
        ),
    ]
