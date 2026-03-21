from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'object_type', 'object_id')
    list_filter = ('action', 'object_type')
    search_fields = ('user__username', 'action', 'object_type')
    ordering = ('-timestamp',)
    readonly_fields = ('user', 'action', 'object_type', 'object_id', 'timestamp', 'metadata')

    actions = ['clear_all_logs']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        # Allow superusers to delete logs or clear them via actions
        return request.user.is_superuser
        
    @admin.action(description="⚠️ Clear ALL Audit Logs (Ignores selection)")
    def clear_all_logs(self, request, queryset):
        # Delete every single log in the table regardless of what checkboxes were clicked
        filter_count = ActivityLog.objects.all().count()
        ActivityLog.objects.all().delete()
        self.message_user(request, f"Successfully wiped all {filter_count} audit logs.", level='success')
