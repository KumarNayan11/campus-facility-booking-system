from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('utilization/', views.utilization_report, name='utilization'),
    path('export/', views.export_data, name='export'),
]
