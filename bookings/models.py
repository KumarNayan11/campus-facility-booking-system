from django.db import models
from django.contrib.auth.models import User
from facilities.models import Facility


class Booking(models.Model):
    """
    Core booking record.

    Conflict detection logic (for viva):
        A new booking (new_start, new_end) conflicts with an existing one if:
            existing.start_time < new_end  AND  existing.end_time > new_start
        This covers all overlap cases: partial left, partial right, and full containment.

    Query:
        Booking.objects.filter(
            facility=facility, date=date, status='confirmed',
            start_time__lt=end_time, end_time__gt=start_time
        )
    """
    STATUS_CHOICES = [
        ('confirmed',  'Confirmed'),
        ('cancelled',  'Cancelled'),
        ('waitlisted', 'Waitlisted'),
    ]

    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    facility   = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='bookings',
    )
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    status     = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='confirmed',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-start_time']

    def __str__(self):
        return (
            f"{self.user.username} | {self.facility.name} | "
            f"{self.date} {self.start_time}–{self.end_time} [{self.status}]"
        )

    def has_conflict(self):
        """
        Returns True if another confirmed booking overlaps with this one.
        Used for validation before saving.
        """
        return Booking.objects.filter(
            facility=self.facility,
            date=self.date,
            status='confirmed',
            start_time__lt=self.end_time,
            end_time__gt=self.start_time,
        ).exclude(pk=self.pk).exists()


class WaitlistEntry(models.Model):
    """
    FIFO queue for bookings that couldn't be confirmed due to a conflict.
    When a confirmed booking is cancelled, the oldest WaitlistEntry for the
    same facility/date/time slot is promoted to a confirmed Booking.

    FIFO order is enforced by ordering on created_at (ascending).
    """
    user       = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='waitlist_entries',
    )
    facility   = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='waitlist_entries',
    )
    date       = models.DateField()
    start_time = models.TimeField()
    end_time   = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']   # oldest first → FIFO

    def __str__(self):
        return (
            f"[WAITLIST] {self.user.username} | {self.facility.name} | "
            f"{self.date} {self.start_time}–{self.end_time}"
        )
