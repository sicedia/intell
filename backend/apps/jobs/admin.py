"""
Admin configuration for jobs app.
"""
from django.contrib import admin
from .models import Job, ImageTask, DescriptionTask


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Job model."""
    list_display = ['id', 'status', 'progress_total', 'dataset', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['id', 'idempotency_key']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'created_by', 'dataset', 'status', 'progress_total')
        }),
        ('Idempotency', {
            'fields': ('idempotency_key',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ImageTask)
class ImageTaskAdmin(admin.ModelAdmin):
    """Admin interface for ImageTask model."""
    list_display = ['id', 'job', 'created_by', 'algorithm_key', 'algorithm_version', 'status', 'progress', 'created_at']
    list_filter = ['status', 'algorithm_key', 'output_format', 'created_by', 'created_at']
    search_fields = ['id', 'job__id', 'algorithm_key', 'trace_id', 'created_by__email', 'created_by__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'job', 'created_by', 'algorithm_key', 'algorithm_version', 'params', 'output_format')
        }),
        ('Status', {
            'fields': ('status', 'progress')
        }),
        ('Artifacts', {
            'fields': ('artifact_png', 'artifact_svg', 'chart_data')
        }),
        ('Error Information', {
            'fields': ('error_code', 'error_message', 'trace_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(DescriptionTask)
class DescriptionTaskAdmin(admin.ModelAdmin):
    """Admin interface for DescriptionTask model."""
    list_display = ['id', 'image_task', 'provider_used', 'model_used', 'status', 'progress', 'created_at']
    list_filter = ['status', 'provider_used', 'created_at']
    search_fields = ['id', 'image_task__id', 'trace_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'image_task', 'user_context')
        }),
        ('Status', {
            'fields': ('status', 'progress')
        }),
        ('AI Information', {
            'fields': ('provider_used', 'model_used', 'result_text', 'prompt_snapshot')
        }),
        ('Error Information', {
            'fields': ('error_code', 'error_message', 'trace_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

