"""
Event emission helper.
Single source of truth for event logging, status updates, and WebSocket notifications.
"""
import uuid
from typing import Optional, Dict, Any
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .models import EventLog

# Import models at module level to avoid circular imports and ensure availability
from apps.jobs.models import Job, ImageTask, DescriptionTask


def emit_event(
    job_id: Optional[int] = None,
    image_task_id: Optional[int] = None,
    description_task_id: Optional[int] = None,
    event_type: str = 'PROGRESS',
    level: str = 'INFO',
    message: str = '',
    payload: Optional[Dict[str, Any]] = None,
    trace_id: Optional[str] = None,
    progress: Optional[int] = None
):
    """
    Emit event: insert EventLog, update status/progress, publish to WebSocket.
    
    This is the SINGLE SOURCE OF TRUTH for event emission.
    Always does:
    a) Insert EventLog
    b) Update status/progress in Job/ImageTask/DescriptionTask when applicable
    c) Publish to WebSocket channel job_<job_id>
    
    Args:
        job_id: Job ID (optional)
        image_task_id: ImageTask ID (optional)
        description_task_id: DescriptionTask ID (optional)
        event_type: Type of event (START, PROGRESS, ERROR, etc.)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Event message
        payload: Additional event data
        trace_id: Trace ID (generated if not provided)
        progress: Progress value (0-100)
    """
    # Generate trace_id if not provided
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    
    # Determine entity type and ID
    entity_type = None
    entity_id = None
    
    if job_id:
        entity_type = 'job'
        entity_id = job_id
    elif image_task_id:
        entity_type = 'image_task'
        entity_id = image_task_id
    elif description_task_id:
        entity_type = 'description_task'
        entity_id = description_task_id
    
    # Insert EventLog (append-only)
    event_log = EventLog.objects.create(
        job_id=job_id,
        image_task_id=image_task_id,
        description_task_id=description_task_id,
        trace_id=trace_id,
        event_type=event_type,
        level=level,
        message=message,
        payload=payload or {}
    )
    
    # Update status/progress in related entities
    if job_id:
        try:
            job = Job.objects.get(id=job_id)
            _update_job_status(job, event_type, progress)
        except Job.DoesNotExist:
            pass
    
    if image_task_id:
        try:
            image_task = ImageTask.objects.get(id=image_task_id)
            _update_image_task_status(image_task, event_type, progress)
            # Also update job if not already updated
            if not job_id and image_task.job_id:
                try:
                    job = Job.objects.get(id=image_task.job_id)
                    _update_job_status(job, event_type, progress)
                    job_id = job.id
                except Job.DoesNotExist:
                    pass
        except ImageTask.DoesNotExist:
            pass
    
    if description_task_id:
        try:
            description_task = DescriptionTask.objects.get(id=description_task_id)
            _update_description_task_status(description_task, event_type, progress)
            # Also update job if not already updated
            if not job_id and description_task.image_task_id:
                try:
                    image_task = ImageTask.objects.get(id=description_task.image_task_id)
                    if image_task.job_id:
                        try:
                            job = Job.objects.get(id=image_task.job_id)
                            _update_job_status(job, event_type, progress)
                            job_id = job.id
                        except Job.DoesNotExist:
                            pass
                except ImageTask.DoesNotExist:
                    pass
        except DescriptionTask.DoesNotExist:
            pass
    
    # Publish to WebSocket if job_id exists
    if job_id:
        channel_layer = get_channel_layer()
        if channel_layer:
            # Build stable payload
            ws_payload = {
                "job_id": job_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "event_type": event_type,
                "level": level,
                "progress": progress,
                "message": message,
                "payload": payload or {},
                "trace_id": trace_id,
                "created_at": event_log.created_at.isoformat()
            }
            
            # Send to job channel
            async_to_sync(channel_layer.group_send)(
                f"job_{job_id}",
                {
                    "type": "job_event",
                    "data": ws_payload
                }
            )


def _update_job_status(job, event_type: str, progress: Optional[int]):
    """Update Job status based on event_type."""
    
    if event_type == 'START':
        job.status = Job.Status.RUNNING
        if progress is not None:
            job.progress_total = progress
    elif event_type == 'PROGRESS':
        job.status = Job.Status.RUNNING
        if progress is not None:
            job.progress_total = progress
    elif event_type == 'ERROR':
        # Don't automatically set to FAILED - let finalize_job handle it
        if progress is not None:
            job.progress_total = progress
    elif event_type == 'DONE':
        # Don't automatically set to SUCCESS - let finalize_job handle it
        if progress is not None:
            job.progress_total = progress
    elif event_type == 'VALIDATION_ERROR':
        job.status = Job.Status.FAILED
    
    job.save(update_fields=['status', 'progress_total', 'updated_at'])


def _update_image_task_status(image_task, event_type: str, progress: Optional[int]):
    """Update ImageTask status based on event_type."""
    
    if event_type == 'START':
        image_task.status = ImageTask.Status.RUNNING
        if progress is not None:
            image_task.progress = progress
    elif event_type == 'PROGRESS':
        image_task.status = ImageTask.Status.RUNNING
        if progress is not None:
            image_task.progress = progress
    elif event_type == 'ERROR':
        image_task.status = ImageTask.Status.FAILED
    elif event_type == 'DONE':
        image_task.status = ImageTask.Status.SUCCESS
        if progress is not None:
            image_task.progress = progress
    elif event_type in ['EXTERNAL_API_ERROR', 'ALGORITHM_ERROR', 'RENDER_ERROR', 'STORAGE_ERROR']:
        image_task.status = ImageTask.Status.FAILED
    
    image_task.save(update_fields=['status', 'progress', 'updated_at'])


def _update_description_task_status(description_task, event_type: str, progress: Optional[int]):
    """Update DescriptionTask status based on event_type."""
    
    if event_type == 'START':
        description_task.status = DescriptionTask.Status.RUNNING
        if progress is not None:
            description_task.progress = progress
    elif event_type == 'PROGRESS':
        description_task.status = DescriptionTask.Status.RUNNING
        if progress is not None:
            description_task.progress = progress
    elif event_type == 'ERROR':
        description_task.status = DescriptionTask.Status.FAILED
    elif event_type == 'DONE':
        description_task.status = DescriptionTask.Status.SUCCESS
        if progress is not None:
            description_task.progress = progress
    elif event_type in ['EXTERNAL_API_ERROR', 'AI_PROVIDER_ERROR']:
        description_task.status = DescriptionTask.Status.FAILED
    
    description_task.save(update_fields=['status', 'progress', 'updated_at'])

