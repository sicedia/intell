"""
Helper functions for jobs app.
"""
import logging
from django.utils import timezone
from .models import Job, Tag, ImageTask

logger = logging.getLogger(__name__)


def get_or_create_date_tag_for_job(job: Job) -> Tag:
    """
    Get or create a date-based tag for a Job.
    
    Creates a tag based on the Job's creation date in format "YYYY-MM-DD".
    All images from the same Job will share this tag, allowing them to be
    grouped together.
    
    Args:
        job: Job instance (should have created_at and created_by loaded)
        
    Returns:
        Tag instance for this date
    """
    # Ensure job.created_at exists
    if not hasattr(job, 'created_at') or job.created_at is None:
        # Refresh only if needed - but prefer not to refresh to avoid losing select_related
        try:
            job.refresh_from_db(fields=['created_at', 'created_by'])
        except Exception:
            # If refresh fails, use current time as fallback
            job.created_at = timezone.now()
    
    # Format: YYYY-MM-DD based on Job creation date
    date_str = job.created_at.date().isoformat()
    tag_name = f"Generado {date_str}"
    
    # Get created_by safely - it can be None for anonymous users
    created_by = None
    if hasattr(job, 'created_by'):
        try:
            created_by = job.created_by
        except Exception:
            created_by = None
    
    # Try to get existing tag or create new one
    tag, created = Tag.objects.get_or_create(
        name=tag_name,
        defaults={
            'created_by': created_by,
            'color': '#3b82f6',  # Blue color for date tags
        }
    )
    
    return tag


def assign_date_tag_to_image_task(image_task: ImageTask) -> None:
    """
    Assign the date-based tag from the Job to an ImageTask.
    
    This ensures all images from the same Job (same batch/lote) are tagged
    with the same date, allowing them to be grouped together in the library.
    
    Args:
        image_task: ImageTask instance (should have job loaded with select_related)
    """
    if not image_task.job_id:
        return
    
    # Ensure job is accessible
    try:
        # Try to access job - this will work if it's already loaded or load it if needed
        job = image_task.job
        if not job:
            return
    except Job.DoesNotExist:
        logger.warning(
            f'Job {image_task.job_id} does not exist for ImageTask {image_task.id}',
            extra={'image_task_id': image_task.id, 'job_id': image_task.job_id}
        )
        return
    
    try:
        tag = get_or_create_date_tag_for_job(job)
        
        # Add tag if not already present
        # Use image_task.tags.add() which is safe even if tag already exists
        image_task.tags.add(tag)
    except Exception as e:
        # Log but don't raise - tag assignment failure shouldn't break publishing
        logger.warning(
            f'Failed to assign date tag to ImageTask {image_task.id}: {str(e)}',
            exc_info=True,
            extra={'image_task_id': image_task.id, 'job_id': image_task.job_id}
        )


def ensure_date_tag_on_publish(image_task: ImageTask) -> None:
    """
    Ensure an ImageTask has the date tag when it's published.
    
    This is called when publishing an image to ensure it has the date tag
    from its Job, even if it wasn't assigned initially.
    
    Args:
        image_task: ImageTask instance
        
    Note:
        This function catches and logs any errors to prevent publishing failures
        if tag assignment fails.
    """
    try:
        assign_date_tag_to_image_task(image_task)
    except Exception as e:
        # Log but don't raise - tag assignment failure shouldn't break publishing
        logger.error(
            f'Failed to ensure date tag on publish for ImageTask {image_task.id}: {str(e)}',
            exc_info=True,
            extra={'image_task_id': image_task.id}
        )
