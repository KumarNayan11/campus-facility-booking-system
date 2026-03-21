from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # ── User views ──────────────────────────────────────────────────────────
    path('',                       views.my_requests,       name='my_requests'),
    path('request/',               views.request_create,    name='create'),
    path('<int:pk>/',              views.request_detail,    name='detail'),
    path('<int:pk>/withdraw/',     views.request_withdraw,  name='withdraw'),

    # ── Admin / Dean views ──────────────────────────────────────────────────
    path('admin/',                  views.admin_dashboard, name='admin_dashboard'),
    path('admin/<int:pk>/approve/', views.admin_approve,   name='admin_approve'),
    path('admin/<int:pk>/reject/',  views.admin_reject,    name='admin_reject'),
]

