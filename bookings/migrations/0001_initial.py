# Clean initial migration — BookingRequest model only

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('facilities', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookingRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('purpose', models.TextField(
                    help_text='Briefly describe the purpose of your booking request.'
                )),
                ('status', models.CharField(
                    choices=[
                        ('pending',   'Pending'),
                        ('approved',  'Approved'),
                        ('rejected',  'Rejected'),
                        ('withdrawn', 'Withdrawn'),
                    ],
                    default='pending',
                    db_index=True,
                    max_length=10,
                )),
                ('created_at',        models.DateTimeField(auto_now_add=True)),
                ('reviewed_at',       models.DateTimeField(blank=True, null=True)),
                ('rejection_reason',  models.TextField(blank=True)),
                ('facility', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='booking_requests',
                    to='facilities.facility',
                )),
                ('reviewed_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='reviewed_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='booking_requests',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'verbose_name': 'Booking Request',
                'verbose_name_plural': 'Booking Requests',
                'ordering': ['-created_at'],
            },
        ),
    ]
