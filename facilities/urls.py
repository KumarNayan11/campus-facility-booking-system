from django.urls import path
from .views import (
    FacilityListView, FacilityDetailView,
    FacilityCreateView, FacilityUpdateView, FacilityDeleteView,
)

app_name = 'facilities'

urlpatterns = [
    path('',              FacilityListView.as_view(),   name='list'),
    path('<int:pk>/',     FacilityDetailView.as_view(), name='detail'),
    path('create/',       FacilityCreateView.as_view(), name='create'),
    path('<int:pk>/edit/',   FacilityUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', FacilityDeleteView.as_view(), name='delete'),
]
