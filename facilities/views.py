from datetime import datetime

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from core.models import ActivityLog
from core.services import log_activity

from .forms import FacilityForm
from .models import Facility
from .services import get_facility_availability_map


class SysAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Class-based view equivalent of the sys_admin_required decorator."""

    def test_func(self):
        try:
            return self.request.user.profile.is_sys_admin()
        except Exception:
            return False

    def handle_no_permission(self):
        messages.error(self.request, 'Only system admins can perform this action.')
        return redirect('core:home')


class FacilityListView(ListView):
    """Show all active facilities with daily availability and search filters."""

    model = Facility
    template_name = 'facilities/list.html'
    context_object_name = 'facilities'
    paginate_by = 9

    def get_queryset(self):
        queryset = Facility.objects.filter(is_active=True).select_related('department').prefetch_related('managers')

        # Filter by facility type
        facility_type = self.request.GET.get('type', '').strip()
        if facility_type:
            queryset = queryset.filter(facility_type=facility_type)

        # Filter by minimum capacity
        min_capacity = self.request.GET.get('min_capacity', '').strip()
        if min_capacity:
            try:
                queryset = queryset.filter(capacity__gte=int(min_capacity))
            except ValueError:
                pass

        # Filter by amenity keyword (substring match on comma-separated field)
        amenity = self.request.GET.get('amenity', '').strip()
        if amenity:
            queryset = queryset.filter(amenities__icontains=amenity)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['type_choices'] = Facility.TYPE_CHOICES
        context['selected_type'] = self.request.GET.get('type', '')
        context['min_capacity'] = self.request.GET.get('min_capacity', '')
        context['amenity'] = self.request.GET.get('amenity', '')

        avail_date_str = self.request.GET.get('avail_date', '')
        try:
            avail_date = datetime.strptime(avail_date_str, '%Y-%m-%d').date()
        except ValueError:
            avail_date = timezone.localdate()

        page_facilities = list(context['facilities'])
        availability_map = get_facility_availability_map(
            facilities=page_facilities,
            booking_date=avail_date,
        )
        for facility in page_facilities:
            facility.slots = availability_map.get(facility.pk, [])
            facility.start_hour_label = facility.open_time.strftime('%H:%M')
            facility.end_hour_label = facility.close_time.strftime('%H:%M')

        context['avail_date'] = avail_date
        return context


class FacilityDetailView(DetailView):
    model = Facility
    template_name = 'facilities/detail.html'

    def get_queryset(self):
        return Facility.objects.select_related('department').prefetch_related('managers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['today'] = timezone.localdate()
        return context


class FacilityCreateView(SysAdminRequiredMixin, CreateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'facilities/form.html'
    success_url = reverse_lazy('facilities:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Facility'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            user=self.request.user,
            action=ActivityLog.ACTION_FACILITY_CREATED,
            obj=self.object,
            metadata={'facility_name': self.object.name},
        )
        messages.success(self.request, f'Facility "{self.object.name}" created successfully.')
        return response


class FacilityUpdateView(SysAdminRequiredMixin, UpdateView):
    model = Facility
    form_class = FacilityForm
    template_name = 'facilities/form.html'
    success_url = reverse_lazy('facilities:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit - {self.object.name}'
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            user=self.request.user,
            action=ActivityLog.ACTION_FACILITY_UPDATED,
            obj=self.object,
            metadata={'facility_name': self.object.name},
        )
        messages.success(self.request, f'Facility "{self.object.name}" updated.')
        return response


class FacilityDeleteView(SysAdminRequiredMixin, DeleteView):
    model = Facility
    template_name = 'facilities/confirm_delete.html'
    success_url = reverse_lazy('facilities:list')

    def form_valid(self, form):
        name = self.object.name
        log_activity(
            user=self.request.user,
            action=ActivityLog.ACTION_FACILITY_DELETED,
            obj=self.object,
            metadata={'facility_name': name},
        )
        messages.warning(self.request, f'Facility "{name}" deleted.')
        return super().form_valid(form)
