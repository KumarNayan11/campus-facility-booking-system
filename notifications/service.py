"""
Notification service — the single point for all booking communication.

Current behaviour: logs to Python's standard logger.

To enable real email delivery in production:
  1. Set EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend' in settings/prod.py
  2. Set NOTIFICATIONS_ENABLED = True in settings/prod.py
  3. Replace the `logger.info(...)` call below with `send_mail(...)` 
     — everything else stays identical.
"""

import logging

from django.conf import settings

from .events import EVENT_SUBJECTS

logger = logging.getLogger(__name__)


def send_booking_notification(booking_request, event: str) -> None:
    """
    Dispatch a notification for a booking lifecycle event.

    Args:
        booking_request: A BookingRequest instance.
        event: One of the constants from notifications.events.
    """
    subject = EVENT_SUBJECTS.get(event, event)
    recipient = booking_request.user.email
    facility = booking_request.facility.name
    booking_date = booking_request.date
    start = booking_request.start_time.strftime('%H:%M')
    end = booking_request.end_time.strftime('%H:%M')

    message = (
        f"[{event.upper()}] {subject}\n"
        f"Facility : {facility}\n"
        f"Date     : {booking_date}\n"
        f"Time     : {start} – {end}\n"
        f"Status   : {booking_request.get_status_display()}\n"
        f"Recipient: {recipient or '(no email set)'}\n"
    )

    if getattr(settings, 'NOTIFICATIONS_ENABLED', False):
        from django.core.mail import send_mail
        if recipient:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=True,
            )
        logger.info('NOTIFICATION SENT | %s', message)
    else:
        # Development mode: just log, no actual emails.
        logger.debug('NOTIFICATION (disabled) | %s', message)
