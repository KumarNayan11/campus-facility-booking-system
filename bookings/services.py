from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction
from django.utils import timezone

from core.models import ActivityLog
from core.services import log_activity
from notifications import events as notification_events
from notifications.service import send_booking_notification

from .models import ApprovalStep, BookingPolicy, BookingRequest


def _lock_queryset(queryset):
    """
    Apply row-level locks when the backend supports them.

    SQLite does not implement `SELECT ... FOR UPDATE`, so we keep the surrounding
    transaction atomic and fall back to a regular queryset there.
    """

    if connection.features.has_select_for_update:
        return queryset.select_for_update()
    return queryset


def get_or_create_policy(facility):
    """Ensure every facility has a booking policy record."""
    policy, _ = BookingPolicy.objects.get_or_create(facility=facility)
    return policy


def get_overlapping_requests(*, facility, start_datetime, end_datetime, statuses=None):
    """Return requests overlapping the supplied booking window."""
    queryset = BookingRequest.objects.filter(
        facility=facility,
        start_datetime__lt=end_datetime,
        end_datetime__gt=start_datetime,
    )
    if statuses:
        queryset = queryset.filter(status__in=statuses)
    return queryset


def _validate_booking_window(booking_request):
    """Validate operating-hours and booking-policy constraints."""
    if booking_request.end_datetime <= booking_request.start_datetime:
        raise ValidationError('End date and time must be after the start date and time.')

    local_start = timezone.localtime(booking_request.start_datetime)
    local_end = timezone.localtime(booking_request.end_datetime)
    if local_start.date() != local_end.date():
        raise ValidationError('Bookings must start and end on the same day.')

    if local_start.date() < timezone.localdate():
        raise ValidationError('Booking date cannot be in the past.')

    facility = booking_request.facility
    opens_at = facility.get_open_datetime(local_start.date())
    closes_at = facility.get_close_datetime(local_start.date())
    if booking_request.start_datetime < opens_at or booking_request.end_datetime > closes_at:
        raise ValidationError(
            f'{facility.name} is only available between '
            f'{facility.open_time.strftime("%H:%M")} and {facility.close_time.strftime("%H:%M")}.'
        )

    policy = get_or_create_policy(facility)
    if booking_request.duration > timedelta(hours=policy.max_duration_hours):
        raise ValidationError(
            f'Bookings for {facility.name} cannot exceed {policy.max_duration_hours} hour(s).'
        )

    latest_allowed_date = timezone.localdate() + timedelta(days=policy.max_advance_days)
    if local_start.date() > latest_allowed_date:
        raise ValidationError(
            f'Bookings for {facility.name} can only be made {policy.max_advance_days} day(s) in advance.'
        )

    active_user_bookings = BookingRequest.objects.filter(
        facility=facility,
        user=booking_request.user,
        status__in=[BookingRequest.STATUS_PENDING, BookingRequest.STATUS_APPROVED],
        end_datetime__gte=timezone.now(),
    )
    if booking_request.pk:
        active_user_bookings = active_user_bookings.exclude(pk=booking_request.pk)
    if active_user_bookings.count() >= policy.max_bookings_per_user:
        raise ValidationError(
            f'You have reached the limit of {policy.max_bookings_per_user} active booking(s) '
            f'for {facility.name}.'
        )


def submit_booking_request(*, user, facility, start_datetime, end_datetime, purpose):
    """Create a booking request safely inside an atomic transaction."""
    with transaction.atomic():
        booking_request = BookingRequest(
            user=user,
            facility=facility,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            purpose=purpose,
            status=BookingRequest.STATUS_PENDING,
        )
        _validate_booking_window(booking_request)

        overlapping = _lock_queryset(
            get_overlapping_requests(
                facility=facility,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                statuses=[BookingRequest.STATUS_PENDING, BookingRequest.STATUS_APPROVED],
            )
        )
        approved_conflict = overlapping.filter(status=BookingRequest.STATUS_APPROVED).first()
        if approved_conflict:
            raise ValidationError(
                'This facility is already booked from '
                f'{approved_conflict.start_time.strftime("%H:%M")} to '
                f'{approved_conflict.end_time.strftime("%H:%M")}. Please select another time slot.'
            )

        pending_count = overlapping.filter(status=BookingRequest.STATUS_PENDING).count()
        if facility.max_pending_requests and pending_count >= facility.max_pending_requests:
            raise ValidationError(
                f'The pending queue limit ({facility.max_pending_requests}) for this facility and time slot '
                'has been reached. Please choose another slot.'
            )

        booking_request.save()

        # Create the first approval step in the chain.
        ApprovalStep.objects.create(
            booking_request=booking_request,
            level=1,
            status=ApprovalStep.STATUS_PENDING,
        )

        log_activity(
            user=user,
            action=ActivityLog.ACTION_BOOKING_CREATED,
            obj=booking_request,
            metadata={
                'facility_id': facility.pk,
                'facility_name': facility.name,
                'start_datetime': booking_request.start_datetime.isoformat(),
                'end_datetime': booking_request.end_datetime.isoformat(),
            },
        )
        send_booking_notification(booking_request, notification_events.BOOKING_CREATED)
        return booking_request


def _require_facility_manager(booking_request, acting_user):
    """Ensure only the assigned facility manager can review a booking."""
    if not booking_request.facility.is_managed_by(acting_user):
        raise PermissionDenied('Only the assigned facility manager can review this booking.')


def approve_booking_request(*, booking_request, acting_user):
    """
    Approve the current pending ApprovalStep.

    Single-level (default): marks BookingRequest as APPROVED immediately.
    Multi-level: advances the chain. Only marks BookingRequest as APPROVED
    when the final level is reached.
    """
    with transaction.atomic():
        locked_request = _lock_queryset(
            BookingRequest.objects.select_related('facility', 'user').filter(pk=booking_request.pk)
        ).get()
        _require_facility_manager(locked_request, acting_user)

        if locked_request.status != BookingRequest.STATUS_PENDING:
            raise ValidationError(
                f'Request #{locked_request.pk} is already {locked_request.get_status_display().lower()}.'
            )

        # Get the current (topmost) pending ApprovalStep.
        current_step = (
            locked_request.approval_steps
            .filter(status=ApprovalStep.STATUS_PENDING)
            .order_by('level')
            .first()
        )
        if not current_step:
            raise ValidationError('No pending approval step found for this request.')

        # Record the approval on this step.
        current_step.status = ApprovalStep.STATUS_APPROVED
        current_step.approver = acting_user
        current_step.timestamp = timezone.now()
        current_step.save(update_fields=['status', 'approver', 'timestamp'])

        policy = get_or_create_policy(locked_request.facility)
        required_levels = policy.required_approval_levels

        if current_step.level < required_levels:
            # More levels to go — create the next step and leave as pending.
            ApprovalStep.objects.create(
                booking_request=locked_request,
                level=current_step.level + 1,
                status=ApprovalStep.STATUS_PENDING,
            )
            log_activity(
                user=acting_user,
                action=ActivityLog.ACTION_BOOKING_APPROVED,
                obj=locked_request,
                metadata={
                    'step_level': current_step.level,
                    'next_level': current_step.level + 1,
                    'final': False,
                },
            )
            return locked_request  # Still pending until final level passes.

        # Final level approved — check for conflicts and fully approve.
        conflicting_requests = _lock_queryset(
            get_overlapping_requests(
                facility=locked_request.facility,
                start_datetime=locked_request.start_datetime,
                end_datetime=locked_request.end_datetime,
                statuses=[BookingRequest.STATUS_PENDING, BookingRequest.STATUS_APPROVED],
            ).exclude(pk=locked_request.pk)
        )
        if conflicting_requests.filter(status=BookingRequest.STATUS_APPROVED).exists():
            raise ValidationError('This booking conflicts with an already approved request.')

        locked_request.approve(manager_user=acting_user)
        pending_conflicts = list(conflicting_requests.filter(status=BookingRequest.STATUS_PENDING))
        rejected_count = len(pending_conflicts)
        rejection_reason = 'Another request for the same facility and time slot was approved.'
        
        for conflict in pending_conflicts:
            conflict.reject(manager_user=acting_user, reason=rejection_reason)
            log_activity(
                user=acting_user,
                action=ActivityLog.ACTION_BOOKING_REJECTED,
                obj=conflict,
                metadata={'reason': rejection_reason, 'auto_rejected': True},
            )
            # Notification suppressed for auto-rejected conflicts per Phase 5 spec.

        log_activity(
            user=acting_user,
            action=ActivityLog.ACTION_BOOKING_APPROVED,
            obj=locked_request,
            metadata={'rejected_conflicts': rejected_count, 'final': True},
        )
        send_booking_notification(locked_request, notification_events.BOOKING_APPROVED)
        return locked_request


def reject_booking_request(*, booking_request, acting_user, reason=''):
    """Reject a pending booking request at the current approval level."""
    with transaction.atomic():
        locked_request = _lock_queryset(
            BookingRequest.objects.select_related('facility', 'user').filter(pk=booking_request.pk)
        ).get()
        _require_facility_manager(locked_request, acting_user)

        if locked_request.status != BookingRequest.STATUS_PENDING:
            raise ValidationError(
                f'Request #{locked_request.pk} is already {locked_request.get_status_display().lower()}.'
            )

        # Mark the current pending step as rejected.
        current_step = (
            locked_request.approval_steps
            .filter(status=ApprovalStep.STATUS_PENDING)
            .order_by('level')
            .first()
        )
        if current_step:
            current_step.status = ApprovalStep.STATUS_REJECTED
            current_step.approver = acting_user
            current_step.comment = reason
            current_step.timestamp = timezone.now()
            current_step.save(update_fields=['status', 'approver', 'comment', 'timestamp'])

        locked_request.reject(manager_user=acting_user, reason=reason)
        log_activity(
            user=acting_user,
            action=ActivityLog.ACTION_BOOKING_REJECTED,
            obj=locked_request,
            metadata={'reason': reason},
        )
        send_booking_notification(locked_request, notification_events.BOOKING_REJECTED)
        return locked_request


def withdraw_booking_request(*, booking_request, acting_user):
    """Withdraw a pending booking request owned by the acting user."""
    if booking_request.user_id != acting_user.id:
        raise PermissionDenied('You can only withdraw your own booking requests.')
    if booking_request.status != BookingRequest.STATUS_PENDING:
        raise ValidationError('Only pending requests can be withdrawn.')

    booking_request.withdraw()
    log_activity(
        user=acting_user,
        action=ActivityLog.ACTION_BOOKING_WITHDRAWN,
        obj=booking_request,
        metadata={'facility_id': booking_request.facility_id},
    )
    send_booking_notification(booking_request, notification_events.BOOKING_WITHDRAWN)
    return booking_request
