from django.contrib import admin
from .models import Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display   = ('name', 'facility_type', 'capacity', 'is_active', 'created_at')
    list_filter    = ('facility_type', 'is_active')
    search_fields  = ('name', 'description')
    list_editable  = ('is_active',)   # toggle active/inactive directly from the list
    ordering       = ('name',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('name', 'facility_type', 'capacity', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
