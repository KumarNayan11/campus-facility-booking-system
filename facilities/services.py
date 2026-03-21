from collections import defaultdict
from datetime import datetime, timedelta

from django.utils import timezone

from bookings.models import BookingRequest


def get_facility_availability_map(*, facilities, booking_date):
    """
    Build availability slots for the supplied facilities using one booking query.

    The timeline keeps the current one-hour visual grid, but overlap checks are done
    in Python against pre-fetched bookings instead of repeated database lookups.
    """

    facilities = list(facilities)
    if not facilities:
        return {}

    day_start = timezone.make_aware(
        datetime.combine(booking_date, datetime.min.time()),
        timezone.get_current_timezone(),
    )
    day_end = day_start + timedelta(days=1)

    bookings = (
        BookingRequest.objects
        .filter(
            facility__in=facilities,
            status__in=[BookingRequest.STATUS_APPROVED, BookingRequest.STATUS_PENDING],
            start_datetime__lt=day_end,
            end_datetime__gt=day_start,
        )
        .select_related('facility')
        .order_by('start_datetime')
    )

    grouped_bookings = defaultdict(list)
    for booking in bookings:
        grouped_bookings[booking.facility_id].append(booking)

    availability = {}
    for facility in facilities:
        open_dt = facility.get_open_datetime(booking_date)
        close_dt = facility.get_close_datetime(booking_date)
        slot_start = open_dt
        slots = []

        while slot_start < close_dt:
            slot_end = min(slot_start + timedelta(hours=1), close_dt)
            state = 'free'
            for booking in grouped_bookings.get(facility.pk, []):
                if booking.start_datetime < slot_end and booking.end_datetime > slot_start:
                    if booking.status == BookingRequest.STATUS_APPROVED:
                        state = 'booked'
                        break
                    state = 'pending'

            slots.append({
                'label': (
                    f'{timezone.localtime(slot_start).strftime("%H:%M")} - '
                    f'{timezone.localtime(slot_end).strftime("%H:%M")}'
                ),
                'state': state,
            })
            slot_start = slot_end

        availability[facility.pk] = slots

    return availability
