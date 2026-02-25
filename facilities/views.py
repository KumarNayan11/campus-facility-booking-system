from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from .models import Facility
from .forms import FacilityForm
from core.models import ActivityLog


# ── Mixins ────────────────────────────────────────────────────────────────────

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Class-based view equivalent of @admin_required.
    Inherits LoginRequiredMixin (redirects to login if not authenticated)
    then UserPassesTestMixin (runs test_func, raises 403 on failure).
    """
    def test_func(self):
        try:
            return self.request.user.profile.is_admin()
        except Exception:
            return False

    def handle_no_permission(self):
        messages.error(self.request, 'Only admins can perform this action.')
        return redirect('core:home')


# ── Public Views ──────────────────────────────────────────────────────────────

class FacilityListView(ListView):
    """
    Shows all active facilities to everyone.
    Supports optional filtering by facility_type via GET param.
    """
    model               = Facility
    template_name       = 'facilities/list.html'
    context_object_name = 'facilities'
    paginate_by         = 9

    def get_queryset(self):
        qs = Facility.objects.filter(is_active=True)
        facility_type = self.request.GET.get('type')
        if facility_type:
            qs = qs.filter(facility_type=facility_type)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['type_choices'] = Facility.TYPE_CHOICES
        ctx['selected_type'] = self.request.GET.get('type', '')
        return ctx


class FacilityDetailView(DetailView):
    model         = Facility
    template_name = 'facilities/detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Pass today's date for the booking form link
        from datetime import date
        ctx['today'] = date.today()
        return ctx


# ── Admin-only CRUD Views ─────────────────────────────────────────────────────

class FacilityCreateView(AdminRequiredMixin, CreateView):
    model         = Facility
    form_class    = FacilityForm
    template_name = 'facilities/form.html'
    success_url   = reverse_lazy('facilities:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add New Facility'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        ActivityLog.objects.create(
            user=self.request.user,
            action='FACILITY_CREATED',
            details=f'Facility "{self.object.name}" created.',
        )
        messages.success(self.request, f'Facility "{self.object.name}" created successfully.')
        return response


class FacilityUpdateView(AdminRequiredMixin, UpdateView):
    model         = Facility
    form_class    = FacilityForm
    template_name = 'facilities/form.html'
    success_url   = reverse_lazy('facilities:list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Edit — {self.object.name}'
        return ctx

    def form_valid(self, form):
        response = super().form_valid(form)
        ActivityLog.objects.create(
            user=self.request.user,
            action='FACILITY_UPDATED',
            details=f'Facility "{self.object.name}" updated.',
        )
        messages.success(self.request, f'Facility "{self.object.name}" updated.')
        return response


class FacilityDeleteView(AdminRequiredMixin, DeleteView):
    model         = Facility
    template_name = 'facilities/confirm_delete.html'
    success_url   = reverse_lazy('facilities:list')

    def form_valid(self, form):
        name = self.object.name
        ActivityLog.objects.create(
            user=self.request.user,
            action='FACILITY_DELETED',
            details=f'Facility "{name}" deleted.',
        )
        messages.warning(self.request, f'Facility "{name}" deleted.')
        return super().form_valid(form)
