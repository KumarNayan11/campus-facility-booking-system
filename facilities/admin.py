from django.contrib import admin

from bookings.models import BookingPolicy

from .models import Facility


class BookingPolicyInline(admin.StackedInline):
    model = BookingPolicy
    extra = 0
    can_delete = False


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'facility_type',
        'capacity',
        'get_managers',
        'max_pending_requests',
        'is_active',
        'created_at',
    )
    list_filter = ('facility_type', 'is_active', 'managers')
    search_fields = ('name', 'description', 'managers__username')
    list_editable = ('is_active', 'max_pending_requests')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [BookingPolicyInline]

    fieldsets = (
        (None, {
            'fields': (
                'name',
                'facility_type',
                'capacity',
                'open_time',
                'close_time',
                'managers',
                'max_pending_requests',
                'description',
                'is_active',
            ),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_managers(self, obj):
        return ", ".join([u.username for u in obj.managers.all()])
    get_managers.short_description = 'Managers'
