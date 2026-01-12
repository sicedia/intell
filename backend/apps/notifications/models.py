"""
Notification models for user notifications system.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Notification(models.Model):
    """
    Notification model for user notifications.
    
    Supports different notification types and can be linked to various objects
    (ImageTask, DescriptionTask, Job, etc.) through generic foreign key pattern.
    """
    
    class Type(models.TextChoices):
        DESCRIPTION_COMPLETED = 'DESCRIPTION_COMPLETED', 'Description Completed'
        DESCRIPTION_FAILED = 'DESCRIPTION_FAILED', 'Description Failed'
        JOB_COMPLETED = 'JOB_COMPLETED', 'Job Completed'
        JOB_FAILED = 'JOB_FAILED', 'Job Failed'
        IMAGE_GENERATED = 'IMAGE_GENERATED', 'Image Generated'
        SYSTEM = 'SYSTEM', 'System'
    
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="User who receives this notification"
    )
    type = models.CharField(
        max_length=50,
        choices=Type.choices,
        help_text="Notification type"
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title"
    )
    message = models.TextField(
        help_text="Notification message"
    )
    # Generic foreign key pattern: link to different object types
    related_object_type = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Type of related object (e.g., 'DescriptionTask', 'ImageTask', 'Job')"
    )
    related_object_id = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="ID of related object"
    )
    # Metadata for additional context
    metadata = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Additional metadata (provider, model, etc.)"
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether the notification has been read"
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when notification was read"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['user', 'type', 'created_at']),
            models.Index(fields=['related_object_type', 'related_object_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Notification {self.id} ({self.type}) for {self.user}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    @property
    def related_object_url(self):
        """Get URL path for related object based on type."""
        if not self.related_object_type or not self.related_object_id:
            return None
        
        # If we have image_task_id in metadata, use it for the URL
        image_task_id = self.metadata.get('image_task_id') if isinstance(self.metadata, dict) else None
        
        mapping = {
            'DescriptionTask': f'/images/{image_task_id or self.related_object_id}',
            'ImageTask': f'/images/{self.related_object_id}',
            'Job': f'/generate/{self.related_object_id}',
        }
        return mapping.get(self.related_object_type)