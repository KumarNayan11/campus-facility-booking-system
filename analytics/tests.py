from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from bookings.services import approve_booking_request, submit_booking_request
from facilities.models import Facility

from .services import get_facility_utilization, get_most_booked_facilities, get_peak_booking_hours


class AnalyticsServiceTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username='manager', password='test123')
        self.requester = User.objects.create_user(username='requester', password='test123')
        self.facility = Facility.objects.create(
            name='Seminar Hall',
            facility_type='hall',
            capacity=100,
            open_time='08:00',
            close_time='18:00',
        )
        self.facility.managers.add(self.manager)
        self.policy = self.facility.booking_policy
        self.policy.max_bookings_per_user = 10
        self.policy.save()

    def make_datetime(self, days_from_now, hour):
        booking_date = timezone.localdate() + timedelta(days=days_from_now)
        return timezone.make_aware(
            datetime.combine(booking_date, time(hour=hour)),
            timezone.get_current_timezone(),
        )

    def test_analytics_services_aggregate_approved_bookings(self):
        first = submit_booking_request(
            user=self.requester,
            facility=self.facility,
            start_datetime=self.make_datetime(1, 9),
            end_datetime=self.make_datetime(1, 10),
            purpose='Morning session',
        )
        second = submit_booking_request(
            user=self.requester,
            facility=self.facility,
            start_datetime=self.make_datetime(2, 9),
            end_datetime=self.make_datetime(2, 11),
            purpose='Extended session',
        )
        approve_booking_request(booking_request=first, acting_user=self.manager)
        approve_booking_request(booking_request=second, acting_user=self.manager)

        utilization = get_facility_utilization()
        most_booked = get_most_booked_facilities()
        peak_hours = get_peak_booking_hours()

        self.assertEqual(most_booked[0]['facility__name'], 'Seminar Hall')
        self.assertEqual(most_booked[0]['total_bookings'], 2)
        self.assertEqual(peak_hours[0]['hour'], 9)
        self.assertGreater(utilization[0]['booked_hours'], 0)
