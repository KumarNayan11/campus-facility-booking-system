from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Facility(models.Model):
    """
    Represents a bookable campus facility.

    `is_active` provides a soft-delete so historical bookings remain intact.
    """

    TYPE_CHOICES = [
        ('lab', 'Computer Lab'),
        ('hall', 'Seminar Hall'),
        ('sports', 'Sports Area'),
    ]

    name = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    # Comma-separated amenity tags, e.g. "projector,AC,whiteboard,PC"
    amenities = models.CharField(
        max_length=300,
        blank=True,
        help_text='Comma-separated tags, e.g. projector,AC,whiteboard',
    )
    open_time = models.TimeField(default='08:00', help_text='Time the facility opens.')
    close_time = models.TimeField(default='20:00', help_text='Time the facility closes.')
    managers = models.ManyToManyField(
        User,
        related_name='managed_facilities',
        blank=True,
        help_text='Assigned managers who can approve or reject bookings for this facility.',
    )
    # Optional link to the owning department — enables department-scoped admin in the future.
    department = models.ForeignKey(
        'users.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='facilities',
        help_text='Department that owns / administers this facility.',
    )
    max_pending_requests = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Facilities'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.get_facility_type_display()})'

    def is_managed_by(self, user):
        """Return True when the user is an assigned manager, dept admin for the facility, or system admin."""
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, 'profile', None)
        if not profile:
            return False
        if profile.is_sys_admin():
            return True
        if profile.is_dept_admin() and self.department_id == profile.department_id:
            return True
        return self.managers.filter(id=user.id).exists()

    def get_open_datetime(self, booking_date):
        """Build an aware datetime for the facility opening time on a given day."""
        return timezone.make_aware(
            datetime.combine(booking_date, self._coerce_time_value(self.open_time)),
            timezone.get_current_timezone(),
        )

    def get_close_datetime(self, booking_date):
        """Build an aware datetime for the facility closing time on a given day."""
        return timezone.make_aware(
            datetime.combine(booking_date, self._coerce_time_value(self.close_time)),
            timezone.get_current_timezone(),
        )

    @staticmethod
    def _coerce_time_value(value):
        """Accept either a `time` instance or an HH:MM[:SS] string."""
        if isinstance(value, time):
            return value
        return time.fromisoformat(str(value))

    @property
    def daily_open_duration(self):
        """Return the daily operating window as a timedelta."""
        today = timezone.localdate()
        open_dt = self.get_open_datetime(today)
        close_dt = self.get_close_datetime(today)
        return max(close_dt - open_dt, timedelta())

    @property
    def daily_open_hours(self):
        """Return the facility's daily operating window length in hours."""
        return self.daily_open_duration.total_seconds() / 3600

    def amenity_list(self):
        """Return a clean list of amenity tags."""
        return [tag.strip() for tag in self.amenities.split(',') if tag.strip()]
