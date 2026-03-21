from django.contrib.auth.models import User
from django.db import models


class ActivityLog(models.Model):
    """Generic audit trail shared across apps."""

    ACTION_BOOKING_CREATED = 'booking_created'
    ACTION_BOOKING_APPROVED = 'booking_approved'
    ACTION_BOOKING_REJECTED = 'booking_rejected'
    ACTION_BOOKING_WITHDRAWN = 'booking_withdrawn'
    ACTION_FACILITY_CREATED = 'facility_created'
    ACTION_FACILITY_UPDATED = 'facility_updated'
    ACTION_FACILITY_DELETED = 'facility_deleted'

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        target = self.object_type or 'system'
        object_id = self.object_id if self.object_id is not None else '-'
        return f'[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} -> {target}:{object_id}'
