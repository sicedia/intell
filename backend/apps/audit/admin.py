"""
Admin configuration for audit app.
EventLog is read-only (append-only model).
"""
from django.contrib import admin
from .models import EventLog


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    """Admin interface for EventLog model (read-only)."""
    list_display = ['id', 'event_type', 'level', 'job', 'image_task', 'description_task', 'trace_id', 'created_at']
    list_filter = ['event_type', 'level', 'created_at']
    search_fields = ['trace_id', 'message', 'job__id', 'image_task__id']
    readonly_fields = ['id', 'job', 'image_task', 'description_task', 'trace_id', 'event_type', 
                       'level', 'message', 'payload', 'created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('id', 'event_type', 'level', 'message', 'trace_id')
        }),
        ('Related Entities', {
            'fields': ('job', 'image_task', 'description_task')
        }),
        ('Additional Data', {
            'fields': ('payload',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable manual addition (only via emit_event)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing (append-only)."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Disable deletion (append-only)."""
        return False

