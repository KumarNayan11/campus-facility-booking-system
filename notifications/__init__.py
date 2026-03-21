"""
Notifications app — extensibility stub for booking communication events.

Currently logs to the standard Python logger.
To enable real email delivery:
  1. Set EMAIL_BACKEND to an SMTP backend in settings/prod.py
  2. Set NOTIFICATIONS_ENABLED = True in settings/prod.py
  3. Replace the log calls in service.py with send_mail() calls
"""
