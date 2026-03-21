"""
Production settings.
All secrets are read from environment variables — never hard-code them here.

Required env vars:
    DJANGO_SECRET_KEY   — long random string
    DJANGO_ALLOWED_HOSTS — comma-separated hostnames, e.g. "campus.example.com"

Optional env vars for SMTP email:
    EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, EMAIL_USE_TLS
"""

import os

from .base import *  # noqa: F401, F403

# ── Secrets ────────────────────────────────────────────────────────────────────
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

DEBUG = False

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('DJANGO_ALLOWED_HOSTS', '').split(',')
    if h.strip()
]


# ── Security headers ───────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


# ── SMTP Email ─────────────────────────────────────────────────────────────────
# Uncomment and set env vars to enable real email delivery.
#
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.example.com')
# EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
# EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
# EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
# EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
# NOTIFICATIONS_ENABLED = True   # flip this to activate notifications/service.py


# ── Static files ───────────────────────────────────────────────────────────────
# Run `python manage.py collectstatic` before deploying.
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405
