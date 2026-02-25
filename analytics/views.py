from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def dashboard(request):
    return render(request, 'analytics/dashboard.html')


@login_required
def utilization_report(request):
    return render(request, 'analytics/utilization.html')


@login_required
def export_data(request):
    # Placeholder — will return CSV/Excel export later
    from django.http import HttpResponse
    return HttpResponse("Export coming soon.")
