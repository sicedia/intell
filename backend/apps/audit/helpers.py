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
    # Order of precedence: most specific first (description_task > image_task > job)
    # This ensures events are correctly attributed to the entity they're about,
    # even when multiple IDs are provided for context
    entity_type = None
    entity_id = None
    
    if description_task_id:
        entity_type = 'description_task'
        entity_id = description_task_id
    elif image_task_id:
        entity_type = 'image_task'
        entity_id = image_task_id
    elif job_id:
        entity_type = 'job'
        entity_id = job_id
    
    # Ensure payload exists and includes progress if provided
    log_payload = payload or {}
    if progress is not None:
        log_payload['progress'] = progress

    # Insert EventLog (append-only)
    event_log = EventLog.objects.create(
        job_id=job_id,
        image_task_id=image_task_id,
        description_task_id=description_task_id,
        trace_id=trace_id,
        event_type=event_type,
        level=level,
        message=message,
        payload=log_payload
    )
    
    # Update status/progress in related entities
    job_updated = False
    if job_id:
        try:
            job = Job.objects.get(id=job_id)
            # Special handling for job_status_changed - update status from payload
            if event_type == 'job_status_changed' and payload:
                new_status = payload.get('status')
                if new_status:
                    job.status = new_status
                if progress is not None:
                    job.progress_total = progress
                job.save(update_fields=['status', 'progress_total', 'updated_at'])
            else:
                _update_job_status(job, event_type, progress)
            job_updated = True
        except Job.DoesNotExist:
            pass
    
    if image_task_id:
        try:
            image_task = ImageTask.objects.get(id=image_task_id)
            _update_image_task_status(image_task, event_type, progress)
            # Also update job progress based on all image tasks if not already updated
            if image_task.job_id and not job_updated:
                try:
                    job = Job.objects.get(id=image_task.job_id)
                    # Don't recalculate progress if job is already finalized
                    # This prevents race conditions where delayed events override final status
                    is_finalized = job.status in [Job.Status.SUCCESS, Job.Status.FAILED, Job.Status.PARTIAL_SUCCESS, Job.Status.CANCELLED]
                    
                    if not is_finalized:
                        # Recalculate job progress_total from all image tasks
                        image_tasks_qs = ImageTask.objects.filter(job=job)
                        if image_tasks_qs.exists():
                            # Calculate average progress, only counting tasks that have started
                            total_progress = sum(task.progress for task in image_tasks_qs)
                            task_count = image_tasks_qs.count()
                            avg_progress = int(total_progress / task_count) if task_count > 0 else 0
                            job.progress_total = avg_progress
                            # Only update status if not already finalized
                            job.status = Job.Status.RUNNING
                            job.save(update_fields=['status', 'progress_total', 'updated_at'])
                            
                            # Emit a job-level progress event so frontend gets immediate update
                            # This helps when WebSocket is working but polling hasn't run yet
                            _emit_job_progress_event(job, avg_progress, trace_id)
                    # Set job_id for WebSocket emission
                    if not job_id:
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


def _emit_job_progress_event(job, progress: int, trace_id: str):
    """
    Emit a lightweight job progress event to WebSocket.
    This ensures the frontend gets immediate progress updates without waiting for polling.
    """
    channel_layer = get_channel_layer()
    if channel_layer:
        ws_payload = {
            "job_id": job.id,
            "entity_type": "job",
            "entity_id": job.id,
            "event_type": "PROGRESS",
            "level": "INFO",
            "progress": progress,
            "message": f"Job progress: {progress}%",
            "payload": {"progress": progress},
            "trace_id": trace_id,
            "created_at": timezone.now().isoformat()
        }
        
        async_to_sync(channel_layer.group_send)(
            f"job_{job.id}",
            {
                "type": "job_event",
                "data": ws_payload
            }
        )


def _update_job_status(job, event_type: str, progress: Optional[int]):
    """
    Update Job status and progress based on event_type.
    
    Note: For job_status_changed events, the status should already be set
    in finalize_job, so we just update progress if provided.
    
    IMPORTANT: Jobs in finalized states (SUCCESS, FAILED, PARTIAL_SUCCESS, CANCELLED)
    should NOT have their status changed by events from child tasks like DescriptionTask.
    This prevents corruption of the job status when generating AI descriptions after
    the job has completed.
    """
    # Check if job is already in a final state - don't change status from finalized jobs
    # This prevents description tasks and other post-completion events from corrupting job state
    is_finalized = job.status in [
        Job.Status.SUCCESS, 
        Job.Status.FAILED, 
        Job.Status.PARTIAL_SUCCESS, 
        Job.Status.CANCELLED
    ]
    
    if event_type == 'START':
        # Only set to RUNNING if not already finalized
        if not is_finalized:
            job.status = Job.Status.RUNNING
            if progress is not None:
                job.progress_total = progress
        # If finalized, don't update status or progress - job is done
    elif event_type == 'PROGRESS':
        # Only set to RUNNING if not already finalized
        if not is_finalized:
            job.status = Job.Status.RUNNING
            if progress is not None:
                job.progress_total = progress
        # If finalized, don't update status or progress - job is done
    elif event_type == 'job_status_changed':
        # Status should already be set by finalize_job, just update progress
        # But we'll recalculate from image tasks to ensure accuracy
        if progress is not None:
            job.progress_total = progress
        # Recalculate from image tasks to ensure consistency
        image_tasks = ImageTask.objects.filter(job=job)
        if image_tasks.exists():
            avg_progress = sum(task.progress for task in image_tasks) / image_tasks.count()
            job.progress_total = int(avg_progress)
    elif event_type == 'ERROR':
        # Don't automatically set to FAILED - let finalize_job handle it
        if progress is not None and not is_finalized:
            job.progress_total = progress
    elif event_type == 'DONE':
        # Don't automatically set to SUCCESS - let finalize_job handle it
        if progress is not None and not is_finalized:
            job.progress_total = progress
    elif event_type == 'VALIDATION_ERROR':
        job.status = Job.Status.FAILED
    
    # Only save if there's something to update
    # For finalized jobs with non-status-changing events, we skip the save entirely
    if not is_finalized or event_type in ['job_status_changed', 'VALIDATION_ERROR']:
        job.save(update_fields=['status', 'progress_total', 'updated_at'])


def _update_image_task_status(image_task, event_type: str, progress: Optional[int]):
    """Update ImageTask status based on event_type."""
    
    if event_type == 'START':
        image_task.status = ImageTask.Status.RUNNING
        if progress is not None:
            image_task.progress = progress
    elif event_type == 'RETRY':
        # RETRY resets task to PENDING/RUNNING state
        image_task.status = ImageTask.Status.PENDING
        image_task.progress = 0
        image_task.error_code = None
        image_task.error_message = None
    elif event_type == 'CANCELLED':
        image_task.status = ImageTask.Status.CANCELLED
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
    
    image_task.save(update_fields=['status', 'progress', 'error_code', 'error_message', 'updated_at'])


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

