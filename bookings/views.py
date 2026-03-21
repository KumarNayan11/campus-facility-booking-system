from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from facilities.models import Facility
from users.decorators import facility_manager_required

from .forms import BookingRequestForm, RejectRequestForm
from .models import BookingRequest
from .services import (
    approve_booking_request,
    reject_booking_request,
    submit_booking_request,
    withdraw_booking_request,
)


@login_required
def request_create(request):
    """Submit a new booking request that starts in pending status."""

    facility_id = request.GET.get('facility')
    form = BookingRequestForm(request.POST or None, facility_id=facility_id)
    ctx = {'form': form, 'title': 'New Booking Request'}

    if request.method == 'POST' and form.is_valid():
        try:
            booking_request = submit_booking_request(
                user=request.user,
                facility=form.cleaned_data['facility'],
                start_datetime=form.cleaned_data['start_datetime'],
                end_datetime=form.cleaned_data['end_datetime'],
                purpose=form.cleaned_data['purpose'],
            )
        except ValidationError as exc:
            for error in exc.messages:
                form.add_error(None, error)
            return render(request, 'bookings/request_form.html', ctx)

        messages.success(
            request,
            f'Your booking request for {booking_request.facility.name} on '
            f'{booking_request.date} has been submitted and is pending approval.'
        )
        return redirect('bookings:my_requests')

    return render(request, 'bookings/request_form.html', ctx)


@login_required
def my_requests(request):
    """List all booking requests belonging to the logged-in user."""

    requests_qs = (
        BookingRequest.objects
        .filter(user=request.user)
        .select_related('facility', 'reviewed_by')
        .prefetch_related('approval_steps')
    )
    return render(request, 'bookings/my_requests.html', {'requests': requests_qs})


@login_required
def request_detail(request, pk):
    """Show a single booking request to its owner or assigned facility manager."""

    booking_request = get_object_or_404(
        BookingRequest.objects
        .select_related('facility', 'reviewed_by', 'user')
        .prefetch_related('approval_steps__approver'),
        pk=pk,
    )
    can_manage_booking = booking_request.facility.is_managed_by(request.user)
    is_dept_admin_for_facility = (
        request.user.profile.is_dept_admin() and 
        booking_request.facility.department == request.user.profile.department
    )
    if booking_request.user != request.user and not can_manage_booking and not is_dept_admin_for_facility:
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('bookings:my_requests')

    return render(request, 'bookings/request_detail.html', {
        'br': booking_request,
        'can_manage_booking': can_manage_booking,
        'approval_steps': booking_request.approval_steps.order_by('level'),
    })


@login_required
def request_withdraw(request, pk):
    """Allow the owner to withdraw their own pending request."""

    booking_request = get_object_or_404(
        BookingRequest.objects.select_related('facility'),
        pk=pk,
        user=request.user,
    )

    if request.method == 'POST':
        try:
            withdraw_booking_request(booking_request=booking_request, acting_user=request.user)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect('bookings:my_requests')

        messages.success(request, 'Your booking request has been withdrawn.')
        return redirect('bookings:my_requests')

    return render(request, 'bookings/confirm_withdraw.html', {'br': booking_request})


@facility_manager_required
def admin_dashboard(request):
    """Manager dashboard for reviewing booking requests in managed facilities."""

    all_requests = BookingRequest.objects.select_related(
        'user', 'facility', 'reviewed_by'
    ).prefetch_related('approval_steps')
    facilities = Facility.objects.filter(is_active=True)
    if request.user.profile.is_sys_admin():
        pass
    elif request.user.profile.is_dept_admin():
        all_requests = all_requests.filter(facility__department=request.user.profile.department)
        facilities = facilities.filter(department=request.user.profile.department)
    else:
        all_requests = all_requests.filter(facility__managers=request.user)
        facilities = facilities.filter(managers=request.user)

    facility_id = request.GET.get('facility', '')
    filter_date = request.GET.get('date', '')
    filter_status = request.GET.get('status', '')

    if facility_id:
        all_requests = all_requests.filter(facility_id=facility_id)
    if filter_date:
        all_requests = all_requests.filter(start_datetime__date=filter_date)
    if filter_status:
        all_requests = all_requests.filter(status=filter_status)

    pending_requests = all_requests.filter(status=BookingRequest.STATUS_PENDING)
    reviewed_requests = all_requests.exclude(status=BookingRequest.STATUS_PENDING)

    return render(request, 'bookings/admin_dashboard.html', {
        'pending_requests': pending_requests,
        'reviewed_requests': reviewed_requests,
        'facilities': facilities,
        'status_choices': BookingRequest.STATUS_CHOICES,
        'filter_facility': facility_id,
        'filter_date': filter_date,
        'filter_status': filter_status,
    })


@facility_manager_required
def admin_approve(request, pk):
    """Approve the current pending approval step for a booking request."""

    booking_request = get_object_or_404(BookingRequest, pk=pk)

    if request.method == 'POST':
        try:
            result = approve_booking_request(booking_request=booking_request, acting_user=request.user)
            step = result.current_approval_step
            if result.status == BookingRequest.STATUS_APPROVED:
                messages.success(
                    request,
                    f'Request #{pk} fully approved. Conflicting pending requests were rejected automatically.'
                )
            else:
                next_level = step.level if step else '?'
                messages.info(
                    request,
                    f'Request #{pk}: Level {next_level - 1} approved. Awaiting Level {next_level} approval.'
                )
        except PermissionDenied as exc:
            messages.error(request, str(exc))
        except ValidationError as exc:
            messages.warning(request, exc.messages[0])

    return redirect('bookings:admin_dashboard')


@facility_manager_required
def admin_reject(request, pk):
    """Reject a pending booking request."""

    booking_request = get_object_or_404(BookingRequest, pk=pk)
    form = RejectRequestForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        try:
            reject_booking_request(
                booking_request=booking_request,
                acting_user=request.user,
                reason=form.cleaned_data.get('reason', ''),
            )
            messages.info(request, f'Request #{pk} has been rejected.')
            return redirect('bookings:admin_dashboard')
        except PermissionDenied as exc:
            messages.error(request, str(exc))
            return redirect('bookings:admin_dashboard')
        except ValidationError as exc:
            messages.warning(request, exc.messages[0])
            return redirect('bookings:admin_dashboard')

    return render(request, 'bookings/confirm_reject.html', {'br': booking_request, 'form': form})
