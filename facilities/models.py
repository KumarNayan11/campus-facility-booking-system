from django.db import models


class Facility(models.Model):
    """
    Represents a bookable campus facility (lab, seminar hall, sports area).
    is_active provides a soft-delete: disabling hides the facility from new bookings
    without destroying historical booking records.
    """
    TYPE_CHOICES = [
        ('lab',    'Computer Lab'),
        ('hall',   'Seminar Hall'),
        ('sports', 'Sports Area'),
    ]

    name          = models.CharField(max_length=100)
    facility_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    capacity      = models.PositiveIntegerField()
    description   = models.TextField(blank=True)
    is_active     = models.BooleanField(default=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Facilities'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_facility_type_display()})"
