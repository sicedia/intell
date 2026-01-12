"""
Job models - orchestration of chart generation and AI description tasks.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Job(models.Model):
    """
    Job model - orchestrates multiple ImageTasks.
    Has FK to Dataset (canonical format).
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        PARTIAL_SUCCESS = 'PARTIAL_SUCCESS', 'Partial Success'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    id = models.BigAutoField(primary_key=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='jobs'
    )
    dataset = models.ForeignKey(
        'datasets.Dataset',
        on_delete=models.CASCADE,
        related_name='jobs',
        help_text="Canonical dataset for this job"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress_total = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Overall progress (0-100)"
    )
    idempotency_key = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Idempotency key for duplicate request prevention"
    )
    visualization_config = models.JSONField(
        null=True,
        blank=True,
        default=None,
        help_text="Visualization settings (color palette, font size, etc.) applied to all charts"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs_job'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['created_by', 'idempotency_key'],
                name='unique_job_idempotency_scoped'
            )
        ]
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['dataset', 'created_at']),
        ]
    
    def __str__(self):
        return f"Job {self.id} ({self.status})"
    
    def cancel(self):
        """Cancel the job and all associated tasks."""
        from celery import current_app
        
        # Mark job as cancelled
        self.status = self.Status.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
        
        # Cancel all pending/running image tasks
        image_tasks = self.image_tasks.all()
        for task in image_tasks:
            if task.status in [ImageTask.Status.PENDING, ImageTask.Status.RUNNING]:
                task.status = ImageTask.Status.CANCELLED
                task.save(update_fields=['status', 'updated_at'])
                
                # Try to revoke Celery task if we have the task_id
                if hasattr(task, 'celery_task_id') and task.celery_task_id:
                    try:
                        current_app.control.revoke(task.celery_task_id, terminate=True)
                    except Exception:
                        pass  # Task may have already completed
        
        # Emit cancellation event
        from apps.audit.helpers import emit_event
        emit_event(
            job_id=self.id,
            event_type='job_status_changed',
            level='INFO',
            message='Job cancelled by user',
            payload={'status': self.Status.CANCELLED}
        )


class ImageTask(models.Model):
    """
    ImageTask model - generates a single chart image.
    Has FK to Job and consumes Job.dataset.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    class OutputFormat(models.TextChoices):
        PNG = 'png', 'PNG'
        SVG = 'svg', 'SVG'
        BOTH = 'both', 'Both'
    
    id = models.BigAutoField(primary_key=True)
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='image_tasks'
    )
    algorithm_key = models.CharField(
        max_length=100,
        help_text="Algorithm identifier"
    )
    algorithm_version = models.CharField(
        max_length=20,
        help_text="Algorithm version"
    )
    params = models.JSONField(
        default=dict,
        help_text="Algorithm parameters"
    )
    output_format = models.CharField(
        max_length=10,
        choices=OutputFormat.choices,
        default=OutputFormat.BOTH
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Task progress (0-100)"
    )
    artifact_png = models.FileField(
        upload_to='artifacts/png/',
        null=True,
        blank=True,
        help_text="PNG artifact file"
    )
    artifact_svg = models.FileField(
        upload_to='artifacts/svg/',
        null=True,
        blank=True,
        help_text="SVG artifact file"
    )
    chart_data = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Structured chart data for AI processing"
    )
    error_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Error code if failed"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if failed"
    )
    trace_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Trace ID for event correlation"
    )
    # Metadata fields for library management
    title = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User-defined title for the image"
    )
    user_description = models.TextField(
        null=True,
        blank=True,
        help_text="User-editable description (can be AI-generated then edited)"
    )
    group = models.ForeignKey(
        'ImageGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='images',
        help_text="Group this image belongs to"
    )
    tags = models.ManyToManyField(
        'Tag',
        blank=True,
        related_name='images',
        help_text="Tags associated with this image"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether the image is published to the library (draft if False)"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the image was published"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs_imagetask'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['algorithm_key', 'algorithm_version']),
            models.Index(fields=['group', 'created_at']),
            models.Index(fields=['is_published', 'created_at']),
        ]
    
    def __str__(self):
        return f"ImageTask {self.id} ({self.algorithm_key} v{self.algorithm_version})"
    
    def publish(self):
        """Publish the image to the library."""
        if not self.is_published:
            self.is_published = True
            self.published_at = timezone.now()
            self.save(update_fields=['is_published', 'published_at', 'updated_at'])
    
    def unpublish(self):
        """Unpublish the image from the library (convert to draft)."""
        if self.is_published:
            self.is_published = False
            self.published_at = None
            self.save(update_fields=['is_published', 'published_at', 'updated_at'])


class DescriptionTask(models.Model):
    """
    DescriptionTask model - generates AI description for a chart.
    Has FK to ImageTask.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        RUNNING = 'RUNNING', 'Running'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    id = models.BigAutoField(primary_key=True)
    image_task = models.ForeignKey(
        ImageTask,
        on_delete=models.CASCADE,
        related_name='description_tasks'
    )
    user_context = models.TextField(
        null=True,
        blank=True,
        help_text="User-provided context for description"
    )
    provider_used = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="AI provider used (openai, anthropic, mock)"
    )
    model_used = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="AI model used"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    progress = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Task progress (0-100)"
    )
    result_text = models.TextField(
        null=True,
        blank=True,
        help_text="Generated description text"
    )
    prompt_snapshot = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Snapshot of prompt sent to AI"
    )
    error_code = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Error code if failed"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error message if failed"
    )
    trace_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Trace ID for event correlation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs_descriptiontask'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['image_task', 'status']),
        ]
    
    def __str__(self):
        return f"DescriptionTask {self.id} (ImageTask {self.image_task_id})"


class Tag(models.Model):
    """
    Tag model for categorizing images.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag name"
    )
    color = models.CharField(
        max_length=7,
        default='#6366f1',
        help_text="Hex color code for tag display"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_tags',
        help_text="User who created this tag"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'jobs_tag'
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
        ]
    
    def __str__(self):
        return self.name


class ImageGroup(models.Model):
    """
    ImageGroup model for organizing images into collections.
    """
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(
        max_length=100,
        help_text="Group name"
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Optional description of the group"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='image_groups',
        help_text="User who created this group"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'jobs_imagegroup'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_by', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} (by {self.created_by})"

