"""
EventLog model - append-only event logging for traceability.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class EventLog(models.Model):
    """
    Append-only event log.
    Only INSERTs are allowed, never UPDATEs.
    State/progress changes occur in Job/ImageTask/DescriptionTask, never here.
    """
    EVENT_TYPE_CHOICES = [
        ('START', 'Start'),
        ('PROGRESS', 'Progress'),
        ('RETRY', 'Retry'),
        ('ERROR', 'Error'),
        ('DONE', 'Done'),
        ('VALIDATION_ERROR', 'Validation Error'),
        ('EXTERNAL_API_ERROR', 'External API Error'),
        ('ALGORITHM_ERROR', 'Algorithm Error'),
        ('RENDER_ERROR', 'Render Error'),
        ('STORAGE_ERROR', 'Storage Error'),
        ('AI_PROVIDER_ERROR', 'AI Provider Error'),
    ]
    
    LEVEL_CHOICES = [
        ('DEBUG', 'Debug'),
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_logs'
    )
    image_task = models.ForeignKey(
        'jobs.ImageTask',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_logs'
    )
    description_task = models.ForeignKey(
        'jobs.DescriptionTask',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='event_logs'
    )
    trace_id = models.CharField(
        max_length=100,
        help_text="Trace ID for correlating events"
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPE_CHOICES,
        help_text="Type of event"
    )
    level = models.CharField(
        max_length=20,
        choices=LEVEL_CHOICES,
        default='INFO',
        help_text="Log level"
    )
    message = models.TextField(
        help_text="Event message"
    )
    payload = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Additional event data"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_eventlog'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', 'created_at']),
            models.Index(fields=['trace_id']),
            models.Index(fields=['event_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"EventLog {self.id} ({self.event_type}, {self.level})"

