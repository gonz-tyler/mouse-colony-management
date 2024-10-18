# Generated by Django 5.1.2 on 2024-10-17 21:43

import django.contrib.auth.models
import django.contrib.auth.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Breed',
            fields=[
                ('breed_id', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('start_date', models.DateTimeField(auto_now_add=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Cage',
            fields=[
                ('cage_id', models.AutoField(primary_key=True, serialize=False)),
                ('cage_number', models.CharField(max_length=10, unique=True)),
                ('cage_type', models.CharField(max_length=25)),
                ('location', models.CharField(max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='Strain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='BreedingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('finished_at', models.DateTimeField(blank=True, null=True)),
                ('breed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.breed')),
            ],
        ),
        migrations.AddField(
            model_name='breed',
            name='cage',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.cage'),
        ),
        migrations.CreateModel(
            name='Mouse',
            fields=[
                ('mouse_id', models.AutoField(primary_key=True, serialize=False)),
                ('tube_id', models.IntegerField()),
                ('dob', models.DateField()),
                ('sex', models.CharField(choices=[('M', 'Male'), ('F', 'Female')], max_length=1)),
                ('earmark', models.CharField(blank=True, choices=[('TL', 'Top Left'), ('TR', 'Top Right'), ('BL', 'Bottom Left'), ('BR', 'Bottom Right')], max_length=20)),
                ('clipped_date', models.DateField(blank=True, null=True)),
                ('state', models.CharField(choices=[('alive', 'Alive'), ('breeding', 'Breeding'), ('to_be_culled', 'To Be Culled'), ('deceased', 'Deceased')], max_length=12)),
                ('cull_date', models.DateTimeField(blank=True, null=True)),
                ('father', models.ForeignKey(blank=True, limit_choices_to={'sex': 'M'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='father_of', to='website.mouse')),
                ('mother', models.ForeignKey(blank=True, limit_choices_to={'sex': 'F'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mother_of', to='website.mouse')),
                ('mouse_keeper', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='kept_mice', to=settings.AUTH_USER_MODEL)),
                ('strain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.strain')),
            ],
            options={
                'unique_together': {('strain', 'tube_id')},
            },
        ),
        migrations.CreateModel(
            name='Genotype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gene', models.CharField(max_length=50)),
                ('allele_1', models.CharField(max_length=50)),
                ('allele_2', models.CharField(max_length=50)),
                ('test_date', models.DateField(auto_now_add=True)),
                ('mouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='genotypes', to='website.mouse')),
            ],
        ),
        migrations.AddField(
            model_name='breed',
            name='female',
            field=models.ForeignKey(limit_choices_to={'sex': 'F'}, on_delete=django.db.models.deletion.CASCADE, related_name='female_breeds', to='website.mouse'),
        ),
        migrations.AddField(
            model_name='breed',
            name='male',
            field=models.ForeignKey(limit_choices_to={'sex': 'M'}, on_delete=django.db.models.deletion.CASCADE, related_name='male_breeds', to='website.mouse'),
        ),
        migrations.CreateModel(
            name='Phenotype',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('characteristic', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('observation_date', models.DateField(auto_now_add=True)),
                ('mouse', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='phenotypes', to='website.mouse')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('role', models.CharField(choices=[('leader', 'Leader'), ('staff', 'Staff'), ('new_staff', 'New Staff')], default='new_staff', max_length=10)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to.', related_name='website_user_set', to='auth.group')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='website.team')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='website_user_permissions_set', to='auth.permission')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='TeamMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('leader', 'Leader'), ('staff', 'Staff'), ('new_staff', 'New Staff')], max_length=10)),
                ('team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.team')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'team')},
            },
        ),
    ]