from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.utils import timezone

from core.models import ActivityLog
from facilities.models import Facility

from .models import BookingRequest
from .services import (
    approve_booking_request,
    reject_booking_request,
    submit_booking_request,
)


class BookingServiceTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username='student', password='test123')
        self.manager = User.objects.create_user(username='manager', password='test123')
        self.other_manager = User.objects.create_user(username='other_manager', password='test123')
        self.facility = Facility.objects.create(
            name='Computer Lab 1',
            facility_type='lab',
            capacity=40,
            open_time='08:00',
            close_time='20:00',
            max_pending_requests=2,
        )
        self.facility.managers.add(self.manager)
        self.policy = self.facility.booking_policy
        self.policy.max_duration_hours = 2
        self.policy.max_advance_days = 14
        self.policy.max_bookings_per_user = 2
        self.policy.save()

    def make_datetime(self, days_from_now, hour, minute=0):
        booking_date = timezone.localdate() + timedelta(days=days_from_now)
        return timezone.make_aware(
            datetime.combine(booking_date, time(hour=hour, minute=minute)),
            timezone.get_current_timezone(),
        )

    def test_submit_booking_request_creates_pending_booking_and_log(self):
        booking = submit_booking_request(
            user=self.student,
            facility=self.facility,
            start_datetime=self.make_datetime(1, 10),
            end_datetime=self.make_datetime(1, 11),
            purpose='Data structures lab',
        )

        self.assertEqual(booking.status, BookingRequest.STATUS_PENDING)
        self.assertTrue(
            ActivityLog.objects.filter(
                action=ActivityLog.ACTION_BOOKING_CREATED,
                object_id=booking.pk,
            ).exists()
        )

    def test_pending_queue_limit_is_enforced_per_facility(self):
        for index in range(2):
            user = User.objects.create_user(username=f'user_{index}', password='test123')
            submit_booking_request(
                user=user,
                facility=self.facility,
                start_datetime=self.make_datetime(2, 10),
                end_datetime=self.make_datetime(2, 11),
                purpose='Practice session',
            )

        with self.assertRaises(ValidationError):
            submit_booking_request(
                user=self.student,
                facility=self.facility,
                start_datetime=self.make_datetime(2, 10),
                end_datetime=self.make_datetime(2, 11),
                purpose='One more request',
            )

    def test_approval_requires_assigned_manager_and_rejects_conflicts(self):
        first_request = submit_booking_request(
            user=self.student,
            facility=self.facility,
            start_datetime=self.make_datetime(3, 9),
            end_datetime=self.make_datetime(3, 10),
            purpose='Lecture prep',
        )
        second_user = User.objects.create_user(username='student_two', password='test123')
        conflicting_request = submit_booking_request(
            user=second_user,
            facility=self.facility,
            start_datetime=self.make_datetime(3, 9, 30),
            end_datetime=self.make_datetime(3, 10, 30),
            purpose='Overlap request',
        )

        with self.assertRaises(PermissionDenied):
            approve_booking_request(booking_request=first_request, acting_user=self.other_manager)

        approve_booking_request(booking_request=first_request, acting_user=self.manager)
        conflicting_request.refresh_from_db()
        first_request.refresh_from_db()

        self.assertEqual(first_request.status, BookingRequest.STATUS_APPROVED)
        self.assertEqual(first_request.reviewed_by, self.manager)
        self.assertEqual(conflicting_request.status, BookingRequest.STATUS_REJECTED)

    def test_booking_policy_is_enforced_for_duration_and_active_limit(self):
        with self.assertRaises(ValidationError):
            submit_booking_request(
                user=self.student,
                facility=self.facility,
                start_datetime=self.make_datetime(4, 10),
                end_datetime=self.make_datetime(4, 13),
                purpose='Too long',
            )

        submit_booking_request(
            user=self.student,
            facility=self.facility,
            start_datetime=self.make_datetime(5, 10),
            end_datetime=self.make_datetime(5, 11),
            purpose='First booking',
        )
        submit_booking_request(
            user=self.student,
            facility=self.facility,
            start_datetime=self.make_datetime(6, 10),
            end_datetime=self.make_datetime(6, 11),
            purpose='Second booking',
        )

        with self.assertRaises(ValidationError):
            submit_booking_request(
                user=self.student,
                facility=self.facility,
                start_datetime=self.make_datetime(7, 10),
                end_datetime=self.make_datetime(7, 11),
                purpose='Third booking',
            )

    def test_reject_booking_request_updates_status(self):
        booking = submit_booking_request(
            user=self.student,
            facility=self.facility,
            start_datetime=self.make_datetime(8, 12),
            end_datetime=self.make_datetime(8, 13),
            purpose='Workshop',
        )

        reject_booking_request(
            booking_request=booking,
            acting_user=self.manager,
            reason='Maintenance window',
        )
        booking.refresh_from_db()

        self.assertEqual(booking.status, BookingRequest.STATUS_REJECTED)
        self.assertEqual(booking.rejection_reason, 'Maintenance window')
