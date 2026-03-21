from datetime import timedelta

from django.db import models
from django.db.models import Count, DurationField, ExpressionWrapper, Sum
from django.db.models.functions import ExtractHour
from django.utils import timezone

from bookings.models import BookingRequest
from facilities.models import Facility


def get_reporting_window(start_date=None, end_date=None):
    """Return a rolling reporting window that includes upcoming approved bookings."""
    today = timezone.localdate()
    start_date = start_date or (today - timedelta(days=30))
    end_date = end_date or (today + timedelta(days=30))
    return start_date, end_date


def get_facility_utilization(*, start_date=None, end_date=None, user=None):
    """Calculate booked-vs-available hours per facility for the reporting window."""
    start_date, end_date = get_reporting_window(start_date, end_date)
    duration_expression = ExpressionWrapper(
        models.F('end_datetime') - models.F('start_datetime'),
        output_field=DurationField(),
    )
    bookings = BookingRequest.objects.filter(
        status=BookingRequest.STATUS_APPROVED,
        start_datetime__date__gte=start_date,
        start_datetime__date__lte=end_date,
    )
    if user:
        if user.profile.is_sys_admin():
            pass
        elif user.profile.is_dept_admin():
            bookings = bookings.filter(facility__department=user.profile.department)
        else:
            bookings = bookings.filter(facility__managers=user)
            
    booked_hours = {
        row['facility_id']: row
        for row in bookings.values('facility_id', 'facility__name').annotate(
            total_duration=Sum(duration_expression), total_bookings=Count('id')
        )
    }

    total_days = (end_date - start_date).days + 1
    results = []
    facilities = Facility.objects.filter(is_active=True).order_by('name')
    if user:
        if user.profile.is_sys_admin():
            pass
        elif user.profile.is_dept_admin():
            facilities = facilities.filter(department=user.profile.department)
        else:
            facilities = facilities.filter(managers=user)

    for facility in facilities:
        booked_duration = booked_hours.get(facility.pk, {}).get('total_duration') or timedelta()
        booked_hours_value = booked_duration.total_seconds() / 3600
        available_hours = facility.daily_open_hours * total_days
        utilization = (booked_hours_value / available_hours) if available_hours else 0
        results.append({
            'facility': facility,
            'booked_hours': round(booked_hours_value, 2),
            'available_hours': round(available_hours, 2),
            'utilization': round(utilization * 100, 2),
            'total_bookings': booked_hours.get(facility.pk, {}).get('total_bookings', 0),
        })

    return sorted(results, key=lambda item: item['utilization'], reverse=True)


def get_most_booked_facilities(*, start_date=None, end_date=None, limit=5, user=None):
    """Return facilities ranked by approved booking count."""
    start_date, end_date = get_reporting_window(start_date, end_date)
    queryset = BookingRequest.objects.filter(
        status=BookingRequest.STATUS_APPROVED,
        start_datetime__date__gte=start_date,
        start_datetime__date__lte=end_date,
    )
    if user:
        if user.profile.is_sys_admin():
            pass
        elif user.profile.is_dept_admin():
            queryset = queryset.filter(facility__department=user.profile.department)
        else:
            queryset = queryset.filter(facility__managers=user)
            
    return list(
        queryset.values('facility_id', 'facility__name')
        .annotate(total_bookings=Count('id'))
        .order_by('-total_bookings', 'facility__name')[:limit]
    )


def get_peak_booking_hours(*, start_date=None, end_date=None, user=None):
    """Return booking counts grouped by the local start hour."""
    start_date, end_date = get_reporting_window(start_date, end_date)
    queryset = BookingRequest.objects.filter(
        status=BookingRequest.STATUS_APPROVED,
        start_datetime__date__gte=start_date,
        start_datetime__date__lte=end_date,
    )
    if user:
        if user.profile.is_sys_admin():
            pass
        elif user.profile.is_dept_admin():
            queryset = queryset.filter(facility__department=user.profile.department)
        else:
            queryset = queryset.filter(facility__managers=user)

    return list(
        queryset.annotate(hour=ExtractHour('start_datetime'))
        .values('hour')
        .annotate(total_bookings=Count('id'))
        .order_by('-total_bookings', 'hour')
    )
