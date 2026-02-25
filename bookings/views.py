from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Booking, WaitlistEntry
from .forms import BookingForm
from core.models import ActivityLog


@login_required
def booking_create(request):
    """
    Create a new booking with conflict detection.

    Conflict logic:
        A slot is taken if any CONFIRMED booking for the same facility/date satisfies:
            existing.start_time < new.end_time  AND  existing.end_time > new.start_time
        This single filter catches ALL overlap cases.

    Outcome:
        - No conflict  → status = 'confirmed'
        - Conflict exists → status = 'waitlisted' (added to WaitlistEntry)
    """
    facility_id = request.GET.get('facility')
    form = BookingForm(facility_id=facility_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, facility_id=facility_id)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user

            # ── Conflict Detection ────────────────────────────────────────────
            conflict_exists = Booking.objects.filter(
                facility=booking.facility,
                date=booking.date,
                status='confirmed',
                start_time__lt=booking.end_time,   # existing starts before new ends
                end_time__gt=booking.start_time,   # existing ends after new starts
            ).exists()

            if conflict_exists:
                # ── Add to Waitlist ───────────────────────────────────────────
                WaitlistEntry.objects.create(
                    user=request.user,
                    facility=booking.facility,
                    date=booking.date,
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                )
                ActivityLog.objects.create(
                    user=request.user,
                    action='BOOKING_WAITLISTED',
                    details=(
                        f'{request.user.username} added to waitlist for '
                        f'{booking.facility.name} on {booking.date} '
                        f'{booking.start_time}–{booking.end_time}.'
                    ),
                )
                messages.warning(
                    request,
                    f'The slot is already booked. You have been added to the waitlist for '
                    f'{booking.facility.name} on {booking.date}.'
                )
                return redirect('bookings:list')

            # ── Confirm Booking ───────────────────────────────────────────────
            booking.status = 'confirmed'
            booking.save()
            ActivityLog.objects.create(
                user=request.user,
                action='BOOKING_CREATED',
                details=(
                    f'{request.user.username} booked {booking.facility.name} '
                    f'on {booking.date} from {booking.start_time} to {booking.end_time}.'
                ),
            )
            messages.success(
                request,
                f'Booking confirmed for {booking.facility.name} on {booking.date}!'
            )
            return redirect('bookings:list')

    return render(request, 'bookings/form.html', {'form': form, 'title': 'New Booking'})


@login_required
def booking_list(request):
    """Show all bookings belonging to the logged-in user."""
    bookings = Booking.objects.filter(user=request.user).select_related('facility')
    waitlist = WaitlistEntry.objects.filter(user=request.user).select_related('facility')
    return render(request, 'bookings/list.html', {
        'bookings': bookings,
        'waitlist': waitlist,
    })


@login_required
def booking_detail(request, pk):
    """Show a single booking — only accessible by its owner."""
    booking = get_object_or_404(Booking, pk=pk, user=request.user)
    return render(request, 'bookings/detail.html', {'booking': booking})


@login_required
def booking_cancel(request, pk):
    """
    Cancel a booking (POST only).
    After cancellation, promote the oldest waitlist entry for the same slot.
    """
    booking = get_object_or_404(Booking, pk=pk, user=request.user)

    if booking.status != 'confirmed':
        messages.error(request, 'Only confirmed bookings can be cancelled.')
        return redirect('bookings:list')

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()

        ActivityLog.objects.create(
            user=request.user,
            action='BOOKING_CANCELLED',
            details=(
                f'{request.user.username} cancelled booking for '
                f'{booking.facility.name} on {booking.date}.'
            ),
        )

        # ── Waitlist Promotion (FIFO) ─────────────────────────────────────────
        next_in_line = WaitlistEntry.objects.filter(
            facility=booking.facility,
            date=booking.date,
            start_time=booking.start_time,
            end_time=booking.end_time,
        ).first()   # .first() returns oldest due to ordering = ['created_at']

        if next_in_line:
            new_booking = Booking.objects.create(
                user=next_in_line.user,
                facility=next_in_line.facility,
                date=next_in_line.date,
                start_time=next_in_line.start_time,
                end_time=next_in_line.end_time,
                status='confirmed',
            )
            ActivityLog.objects.create(
                user=next_in_line.user,
                action='BOOKING_PROMOTED',
                details=(
                    f'{next_in_line.user.username} promoted from waitlist to confirmed '
                    f'for {new_booking.facility.name} on {new_booking.date}.'
                ),
            )
            next_in_line.delete()
            messages.info(
                request,
                f'Your booking was cancelled. The next person on the waitlist has been confirmed.'
            )
        else:
            messages.success(request, 'Booking cancelled successfully.')

        return redirect('bookings:list')

    return render(request, 'bookings/confirm_cancel.html', {'booking': booking})


@login_required
def booking_approve(request, pk):
    """Admin can manually approve a waitlisted booking."""
    from users.decorators import admin_required
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST' and hasattr(request.user, 'profile') and request.user.profile.is_admin():
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, f'Booking #{pk} approved.')
    return redirect('bookings:list')
