from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required


def login_view(request):
    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('users:login')


def register_view(request):
    return render(request, 'users/register.html')


@login_required
def profile_view(request):
    return render(request, 'users/profile.html')
