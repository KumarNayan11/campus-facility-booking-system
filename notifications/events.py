"""
Booking notification event constants.

Usage:
    from notifications.events import BOOKING_CREATED
    send_booking_notification(booking_request, BOOKING_CREATED)
"""

BOOKING_CREATED = 'booking_created'
BOOKING_APPROVED = 'booking_approved'
BOOKING_REJECTED = 'booking_rejected'
BOOKING_WITHDRAWN = 'booking_withdrawn'

# Map each event to a human-readable subject line for future email use.
EVENT_SUBJECTS = {
    BOOKING_CREATED: 'Booking Request Submitted — Pending Approval',
    BOOKING_APPROVED: 'Your Booking Request Has Been Approved',
    BOOKING_REJECTED: 'Your Booking Request Has Been Rejected',
    BOOKING_WITHDRAWN: 'Booking Request Withdrawn',
}
