from django.db import models
from django.contrib.auth.models import User


class ActivityLog(models.Model):
    """
    Generic audit trail shared across all apps.
    Placed in `core` to avoid circular imports — bookings, facilities,
    and users all write logs without depending on each other.

    action constants (use these when logging):
        BOOKING_CREATED, BOOKING_CANCELLED, BOOKING_APPROVED,
        FACILITY_CREATED, FACILITY_UPDATED, FACILITY_DELETED,
        USER_REGISTERED
    """
    user      = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    action    = models.CharField(max_length=100)   # e.g. "BOOKING_CREATED"
    details   = models.TextField(blank=True)        # human-readable description
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} — {self.user}"
