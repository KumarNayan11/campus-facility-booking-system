"""campus_booking URL Configuration"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('users/', include('users.urls', namespace='users')),
    path('facilities/', include('facilities.urls', namespace='facilities')),
    path('bookings/', include('bookings.urls', namespace='bookings')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('', include('core.urls', namespace='core')),
]
