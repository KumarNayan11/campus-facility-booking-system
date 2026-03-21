"""
Development settings — never use in production.
"""

from .base import *  # noqa: F401, F403

SECRET_KEY = 'django-insecure-=%(d$z@!)s_8pqtkqj)y$z)dv8yhx(e9841bmxwg&26lez416b'

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Dev uses the console email backend defined in base.py.
# Real emails are printed to the terminal — no SMTP needed.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
