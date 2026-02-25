from django.contrib import admin
from .models import Booking, WaitlistEntry


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display   = ('user', 'facility', 'date', 'start_time', 'end_time', 'status', 'created_at')
    list_filter    = ('status', 'facility', 'date')
    search_fields  = ('user__username', 'facility__name')
    ordering       = ('-date', '-start_time')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'    # adds a drill-down date navigator at the top

    fieldsets = (
        ('Booking Details', {
            'fields': ('user', 'facility', 'date', 'start_time', 'end_time', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['mark_cancelled']

    @admin.action(description='Cancel selected bookings')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} booking(s) marked as cancelled.')


@admin.register(WaitlistEntry)
class WaitlistEntryAdmin(admin.ModelAdmin):
    list_display  = ('user', 'facility', 'date', 'start_time', 'end_time', 'created_at')
    list_filter   = ('facility', 'date')
    search_fields = ('user__username', 'facility__name')
    ordering      = ('created_at',)    # FIFO — oldest first
    readonly_fields = ('created_at',)
