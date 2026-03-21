import csv
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .services import (
    get_facility_utilization,
    get_most_booked_facilities,
    get_peak_booking_hours,
    get_reporting_window,
)


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None


def _require_analytics_access(request):
    if request.user.profile.can_view_analytics():
        return None
    messages.error(request, 'You do not have permission to view analytics.')
    return redirect('core:home')


@login_required
def dashboard(request):
    denial = _require_analytics_access(request)
    if denial:
        return denial

    start_date = _parse_date(request.GET.get('start'))
    end_date = _parse_date(request.GET.get('end'))
    start_date, end_date = get_reporting_window(start_date, end_date)

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'utilization_rows': get_facility_utilization(start_date=start_date, end_date=end_date, user=request.user),
        'most_booked_facilities': get_most_booked_facilities(start_date=start_date, end_date=end_date, user=request.user),
        'peak_booking_hours': get_peak_booking_hours(start_date=start_date, end_date=end_date, user=request.user),
    }
    return render(request, 'analytics/dashboard.html', context)


@login_required
def utilization_report(request):
    denial = _require_analytics_access(request)
    if denial:
        return denial

    start_date = _parse_date(request.GET.get('start'))
    end_date = _parse_date(request.GET.get('end'))
    start_date, end_date = get_reporting_window(start_date, end_date)

    return render(request, 'analytics/utilization.html', {
        'start_date': start_date,
        'end_date': end_date,
        'utilization_rows': get_facility_utilization(start_date=start_date, end_date=end_date, user=request.user),
    })


@login_required
def export_data(request):
    """
    Export booking requests as a CSV file.

    Query params:
        start (YYYY-MM-DD) — earliest booking date   (default: 30 days ago)
        end   (YYYY-MM-DD) — latest booking date      (default: 30 days ahead)
        status             — filter by status string  (optional)
    """
    denial = _require_analytics_access(request)
    if denial:
        return denial

    from bookings.models import BookingRequest

    start_date = _parse_date(request.GET.get('start'))
    end_date = _parse_date(request.GET.get('end'))
    start_date, end_date = get_reporting_window(start_date, end_date)
    filter_status = request.GET.get('status', '').strip()

    queryset = (
        BookingRequest.objects
        .filter(
            start_datetime__date__gte=start_date,
            start_datetime__date__lte=end_date,
        )
        .select_related('user', 'facility', 'reviewed_by')
        .order_by('start_datetime')
    )
    if request.user.profile.is_sys_admin():
        pass
    elif request.user.profile.is_dept_admin():
        queryset = queryset.filter(facility__department=request.user.profile.department)
    else:
        queryset = queryset.filter(facility__managers=request.user)
    if filter_status:
        queryset = queryset.filter(status=filter_status)

    filename = f'bookings_{start_date}_{end_date}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Header row
    writer.writerow([
        'ID', 'Facility', 'Facility Type', 'Date',
        'Start Time', 'End Time', 'Duration (hrs)',
        'Status', 'User', 'Purpose',
        'Reviewed By', 'Reviewed At', 'Rejection Reason',
    ])

    for br in queryset:
        writer.writerow([
            br.pk,
            br.facility.name,
            br.facility.get_facility_type_display(),
            br.date,
            br.start_time.strftime('%H:%M'),
            br.end_time.strftime('%H:%M'),
            round(br.duration_hours, 2),
            br.get_status_display(),
            br.user.username,
            br.purpose,
            br.reviewed_by.username if br.reviewed_by else '',
            br.reviewed_at.strftime('%Y-%m-%d %H:%M') if br.reviewed_at else '',
            br.rejection_reason,
        ])

    return response
