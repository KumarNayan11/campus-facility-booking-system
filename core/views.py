from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone


def home(request):
    context = {}
    if request.user.is_authenticated:
        from bookings.models import BookingRequest
        from django.utils import timezone
        upcoming_bookings = BookingRequest.objects.filter(
            user=request.user,
            status__in=[BookingRequest.STATUS_APPROVED, BookingRequest.STATUS_PENDING],
            end_datetime__gte=timezone.now()
        ).select_related('facility').order_by('start_datetime')[:5]
        context['upcoming_bookings'] = upcoming_bookings

    return render(request, 'core/home.html', context)


@login_required
def calendar_view(request):
    """
    Unified weekly calendar showing all approved bookings across all facilities.

    Query params:
        week (YYYY-MM-DD) — any date within the desired week; defaults to current week.
    """
    from bookings.models import BookingRequest

    week_param = request.GET.get('week', '')
    try:
        from datetime import datetime
        anchor = datetime.strptime(week_param, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        anchor = timezone.localdate()

    # Week starts on Monday.
    week_start = anchor - timedelta(days=anchor.weekday())
    week_end = week_start + timedelta(days=6)

    approved_bookings = (
        BookingRequest.objects
        .filter(
            status=BookingRequest.STATUS_APPROVED,
            start_datetime__date__gte=week_start,
            start_datetime__date__lte=week_end,
        )
        .select_related('facility', 'user')
        .order_by('start_datetime')
    )

    # Build a day-keyed dict: {date: [booking, ...]}
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    calendar_data = {day: [] for day in week_days}
    for booking in approved_bookings:
        day = booking.date
        if day in calendar_data:
            calendar_data[day].append(booking)

    # Convert to an ordered list of (date, bookings) for easy template iteration.
    calendar_rows = [(day, calendar_data[day]) for day in week_days]

    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    return render(request, 'core/calendar.html', {
        'calendar_rows': calendar_rows,
        'week_start': week_start,
        'week_end': week_end,
        'prev_week': prev_week,
        'next_week': next_week,
        'today': timezone.localdate(),
    })
