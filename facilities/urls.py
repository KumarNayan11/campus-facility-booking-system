from django.urls import path
from . import views

app_name = 'facilities'

urlpatterns = [
    path('', views.facility_list, name='list'),
    path('<int:pk>/', views.facility_detail, name='detail'),
    path('create/', views.facility_create, name='create'),
    path('<int:pk>/edit/', views.facility_edit, name='edit'),
    path('<int:pk>/delete/', views.facility_delete, name='delete'),
]
