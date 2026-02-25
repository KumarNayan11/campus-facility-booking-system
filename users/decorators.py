"""
Custom access-control decorators for role-based views.

Usage:
    @admin_required
    def my_admin_view(request): ...

    @student_required
    def my_student_view(request): ...
"""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    """Allow only users with role='admin' to access the view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        try:
            if request.user.profile.is_admin():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('core:home')
    return wrapper


def student_required(view_func):
    """Allow only users with role='student' to access the view."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        try:
            if request.user.profile.is_student():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'This page is for students only.')
        return redirect('core:home')
    return wrapper
