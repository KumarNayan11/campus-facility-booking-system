"""Custom access-control decorators for role-aware views."""

from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def sys_admin_required(view_func):
    """Allow only users with role='sys_admin' to access the view."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        try:
            if request.user.profile.is_sys_admin():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('core:home')

    return wrapper


def facility_manager_required(view_func):
    """Allow only users managing at least one facility to access the view."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        try:
            if request.user.profile.is_facility_manager():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'Only assigned facility managers can access this page.')
        return redirect('core:home')

    return wrapper


def user_required(view_func):
    """Allow only users with role='user' to access the view."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        try:
            if request.user.profile.is_user():
                return view_func(request, *args, **kwargs)
        except Exception:
            pass
        messages.error(request, 'This page is for regular users only.')
        return redirect('core:home')

    return wrapper
