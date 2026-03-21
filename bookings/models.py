from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from facilities.models import Facility


class BookingRequest(models.Model):
    """
    Approval-based booking request.

    Conflict rule:
        existing.start_datetime < new.end_datetime
        AND
        existing.end_datetime > new.start_datetime
    """

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_WITHDRAWN = 'withdrawn'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_WITHDRAWN, 'Withdrawn'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='booking_requests',
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        related_name='booking_requests',
    )
    start_datetime = models.DateTimeField(db_index=True)
    end_datetime = models.DateTimeField(db_index=True)
    purpose = models.TextField(
        blank=False,
        help_text='Briefly describe the purpose of your booking request.',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests',
    )
    rejection_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Booking Request'
        verbose_name_plural = 'Booking Requests'
        indexes = [
            models.Index(fields=['facility', 'status', 'start_datetime']),
            models.Index(fields=['facility', 'status', 'end_datetime']),
            models.Index(fields=['user', 'status', 'start_datetime']),
        ]

    def __str__(self):
        return (
            f'[{self.get_status_display().upper()}] '
            f'{self.user.username} -> {self.facility.name} | '
            f'{self.date} {self.start_time}-{self.end_time}'
        )

    @property
    def local_start(self):
        return timezone.localtime(self.start_datetime)

    @property
    def local_end(self):
        return timezone.localtime(self.end_datetime)

    @property
    def date(self):
        return self.local_start.date()

    @property
    def start_time(self):
        return self.local_start.time()

    @property
    def end_time(self):
        return self.local_end.time()

    @property
    def duration(self):
        return self.end_datetime - self.start_datetime

    @property
    def duration_hours(self):
        return self.duration.total_seconds() / 3600

    def overlapping_requests(self, statuses=None):
        """Return other requests that conflict with this booking window."""
        queryset = BookingRequest.objects.filter(
            facility=self.facility,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime,
        ).exclude(pk=self.pk)
        if statuses:
            queryset = queryset.filter(status__in=statuses)
        return queryset

    def approve(self, manager_user):
        """Mark the request as approved."""
        self.status = self.STATUS_APPROVED
        self.reviewed_by = manager_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = ''
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

    def reject(self, manager_user, reason=''):
        """Reject this request with an optional reason."""
        self.status = self.STATUS_REJECTED
        self.reviewed_by = manager_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'rejection_reason'])

    def withdraw(self):
        """Allow the owner to withdraw a pending request."""
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_WITHDRAWN
            self.save(update_fields=['status'])

    @property
    def current_approval_level(self):
        """Return the latest ApprovalStep level (or 0 if none exist)."""
        step = self.approval_steps.order_by('-level').first()
        return step.level if step else 0

    @property
    def current_approval_step(self):
        """Return the active (most recent) ApprovalStep, or None."""
        return self.approval_steps.order_by('-level').first()


class BookingPolicy(models.Model):
    """Facility-specific booking constraints enforced during request creation."""

    facility = models.OneToOneField(
        Facility,
        on_delete=models.CASCADE,
        related_name='booking_policy',
    )
    max_duration_hours = models.PositiveIntegerField(default=4)
    max_advance_days = models.PositiveIntegerField(default=30)
    max_bookings_per_user = models.PositiveIntegerField(default=3)

    # Multi-level approval: 1 = single level (current default behaviour),
    # 2 or 3 = chain approval.  Each level requires a separate approve action.
    required_approval_levels = models.PositiveSmallIntegerField(
        default=1,
        help_text='Number of approval levels required (1–3). Default is single-level.',
    )

    class Meta:
        ordering = ['facility__name']

    def __str__(self):
        return f'Policy for {self.facility.name}'


class ApprovalStep(models.Model):
    """
    Records each individual approval action in a multi-level workflow.

    For a single-level facility (required_approval_levels=1), exactly one
    ApprovalStep at level=1 is created per BookingRequest.

    For a two-level facility, two steps are created sequentially:
      level 1 → approved → level 2 created → approved → BookingRequest approved.
    """

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    booking_request = models.ForeignKey(
        BookingRequest,
        on_delete=models.CASCADE,
        related_name='approval_steps',
    )
    level = models.PositiveSmallIntegerField(
        help_text='Approval chain position: 1 = first approver, 2 = second, etc.',
    )
    approver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_steps',
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['booking_request', 'level']
        unique_together = [('booking_request', 'level')]
        verbose_name = 'Approval Step'
        verbose_name_plural = 'Approval Steps'

    def __str__(self):
        return (
            f'Step {self.level} [{self.get_status_display()}] '
            f'— BookingRequest #{self.booking_request_id}'
        )


# ── Recurring Bookings (future feature stub) ───────────────────────────────────
# Uncomment and run migrations when recurring booking support is needed.
# See settings/base.py RECURRENCE_SETTINGS for configuration options.

class RecurringRule(models.Model):
    DAILY   = 'daily'
    WEEKLY  = 'weekly'
    MONTHLY = 'monthly'
    FREQUENCY_CHOICES = [(DAILY, 'Daily'), (WEEKLY, 'Weekly'), (MONTHLY, 'Monthly')]

    booking_request = models.OneToOneField(
        BookingRequest, on_delete=models.CASCADE, related_name='recurring_rule'
    )
    frequency   = models.CharField(max_length=10, choices=FREQUENCY_CHOICES)
    interval    = models.PositiveSmallIntegerField(default=1)   # every N days/weeks/months
    until_date  = models.DateField()
    max_count   = models.PositiveSmallIntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.frequency} x{self.interval} until {self.until_date}'


@receiver(post_save, sender=Facility)
def ensure_booking_policy(sender, instance, created, **kwargs):
    """Create a default booking policy for every facility."""
    if created:
        BookingPolicy.objects.get_or_create(facility=instance)
