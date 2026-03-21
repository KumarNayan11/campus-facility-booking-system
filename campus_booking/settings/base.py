"""
Base settings for campus_booking project.
Environment-specific overrides live in dev.py and prod.py.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


# ─── Application Definition ────────────────────────────────────────────────────

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project apps
    'users',
    'facilities',
    'bookings',
    'analytics',
    'core',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'campus_booking.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'campus_booking.wsgi.application'


# ─── Database ──────────────────────────────────────────────────────────────────
# Override in environment-specific settings.

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ─── Authentication ────────────────────────────────────────────────────────────

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ── SSO / OAuth extensibility stub ────────────────────────────────────────────
# To enable SSO (e.g. django-allauth, social-auth-app-django):
#   1. pip install django-allauth
#   2. Uncomment and extend AUTHENTICATION_BACKENDS below
#   3. Add the provider to INSTALLED_APPS
#   4. Configure provider keys in your .env
#
# AUTHENTICATION_BACKENDS = [
#     'django.contrib.auth.backends.ModelBackend',          # keep for admin login
#     'allauth.account.auth_backends.AuthenticationBackend', # allauth / SSO
# ]


# ─── Internationalisation ──────────────────────────────────────────────────────

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# ─── Static Files ──────────────────────────────────────────────────────────────

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─── Email ─────────────────────────────────────────────────────────────────────
# Default: console backend (safe for all environments that haven't overridden).
# Override in prod.py with django.core.mail.backends.smtp.EmailBackend
# and set EMAIL_HOST / EMAIL_PORT / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD in .env

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'Campus Booking <noreply@campus.example.com>'


# ─── Notifications ─────────────────────────────────────────────────────────────
# Controls behaviour of notifications/service.py
# Set NOTIFICATIONS_ENABLED = True in prod.py once an email backend is wired up.

NOTIFICATIONS_ENABLED = True


# ─── Recurring Bookings ────────────────────────────────────────────────────────
# Future feature stub. Activate by implementing RecurringRule in bookings/models.py
# and setting RECURRENCE_ENABLED = True here.
#
RECURRENCE_SETTINGS = {
    'ENABLED': True,
    'MAX_OCCURRENCES': 52,   # maximum recurrences per rule
    'ALLOWED_FREQUENCIES': ['daily', 'weekly', 'monthly'],
}
