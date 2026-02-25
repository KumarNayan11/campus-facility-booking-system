from django.contrib import admin
from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display  = ('timestamp', 'user', 'action', 'short_details')
    list_filter   = ('action',)
    search_fields = ('user__username', 'action', 'details')
    ordering      = ('-timestamp',)
    readonly_fields = ('user', 'action', 'details', 'timestamp')  # logs are immutable

    # Prevent creating or deleting logs from admin — audit trail must stay intact
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description='Details')
    def short_details(self, obj):
        return obj.details[:80] + '…' if len(obj.details) > 80 else obj.details
