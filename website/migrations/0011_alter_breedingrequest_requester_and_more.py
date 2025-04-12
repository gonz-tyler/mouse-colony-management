# Generated by Django 5.1.2 on 2025-04-10 14:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0010_alter_mouse_sex_alter_user_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='breedingrequest',
            name='requester',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='breeding_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='cullingrequest',
            name='requester',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='culling_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='transferrequest',
            name='requester',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transfer_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('request_type', models.CharField(blank=True, help_text='Type of request associated with the notification.', max_length=20, null=True)),
                ('request_id', models.IntegerField(blank=True, help_text='ID of the associated request.', null=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
