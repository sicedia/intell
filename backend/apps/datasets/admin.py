"""
Admin configuration for datasets app.
"""
from django.contrib import admin
from .models import Dataset


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    """Admin interface for Dataset model."""
    list_display = ['id', 'source_type', 'normalized_format', 'schema_version', 'created_at']
    list_filter = ['source_type', 'normalized_format', 'created_at']
    search_fields = ['id', 'source_type']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'source_type', 'schema_version', 'normalized_format')
        }),
        ('Storage', {
            'fields': ('storage_path',)
        }),
        ('Metadata', {
            'fields': ('summary_stats', 'columns_map')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

