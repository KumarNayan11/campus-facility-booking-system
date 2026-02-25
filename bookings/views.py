from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required


@login_required
def booking_list(request):
    return render(request, 'bookings/list.html')


@login_required
def booking_create(request):
    return render(request, 'bookings/form.html')


@login_required
def booking_detail(request, pk):
    return render(request, 'bookings/detail.html', {'pk': pk})


@login_required
def booking_cancel(request, pk):
    return redirect('bookings:list')


@login_required
def booking_approve(request, pk):
    return redirect('bookings:list')
