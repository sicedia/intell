"""
Celery tasks for job orchestration.
"""
import logging
from celery import group, chord
from celery import shared_task
from django.core.files.base import ContentFile
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.algorithms.registry import AlgorithmRegistry
from apps.audit.helpers import emit_event
import traceback

logger = logging.getLogger(__name__)


def _check_and_update_job_status(job: Job) -> None:
    """
    Check if all ImageTasks for a job are complete and update job status accordingly.
    
    This is called after individual task completion to handle:
    - Individual task retries (which don't trigger finalize_job)
    - Edge cases where chord callback might not fire
    
    Args:
        job: Job instance to check
    """
    # Refresh job from DB to get latest status
    job.refresh_from_db()
    
    # Skip if job is already in a final state
    if job.status in [Job.Status.SUCCESS, Job.Status.CANCELLED]:
        return
    
    # Get all ImageTasks for this job
    image_tasks = ImageTask.objects.filter(job=job)
    
    if not image_tasks.exists():
        return
    
    # Count statuses
    total_count = image_tasks.count()
    success_count = image_tasks.filter(status=ImageTask.Status.SUCCESS).count()
    failed_count = image_tasks.filter(status=ImageTask.Status.FAILED).count()
    cancelled_count = image_tasks.filter(status=ImageTask.Status.CANCELLED).count()
    completed_count = success_count + failed_count + cancelled_count
    
    # Only update if all tasks are complete
    if completed_count < total_count:
        # Still have pending/running tasks - update progress only
        avg_progress = sum(task.progress for task in image_tasks) / total_count
        if job.progress_total != int(avg_progress):
            job.progress_total = int(avg_progress)
            job.save(update_fields=['progress_total', 'updated_at'])
        return
    
    # All tasks complete - determine final status
    old_status = job.status
    
    if cancelled_count == total_count:
        job.status = Job.Status.CANCELLED
    elif success_count == total_count:
        job.status = Job.Status.SUCCESS
    elif success_count > 0:
        job.status = Job.Status.PARTIAL_SUCCESS
    else:
        job.status = Job.Status.FAILED
    
    job.progress_total = 100
    job.save(update_fields=['status', 'progress_total', 'updated_at'])
    
    # Emit job_status_changed event if status changed
    if old_status != job.status:
        emit_event(
            job_id=job.id,
            event_type='job_status_changed',
            level='INFO',
            message=f'Job status changed from {old_status} to {job.status}',
            progress=100,
            payload={'status': job.status, 'previous_status': old_status}
        )
        
        # Also emit DONE for the job
        emit_event(
            job_id=job.id,
            event_type='DONE',
            level='INFO',
            message=f'Job completed: {job.status} ({success_count}/{total_count} successful)',
            progress=100,
            payload={
                'success_count': success_count,
                'failed_count': failed_count,
                'cancelled_count': cancelled_count,
                'total_count': total_count
            }
        )


@shared_task(bind=True, name='apps.jobs.tasks.generate_image_task')
def generate_image_task(self, image_task_id: int):
    """
    Generate chart image for an ImageTask.
    Consumes Dataset - either from params._dataset_id or Job.dataset.
    
    Args:
        image_task_id: ImageTask ID
    """
    from apps.datasets.models import Dataset
    
    try:
        # Get ImageTask and Job
        try:
            image_task = ImageTask.objects.select_related('job', 'job__dataset').get(id=image_task_id)
        except ImageTask.DoesNotExist:
            logger.warning(
                f'ImageTask {image_task_id} does not exist - task may have been cancelled or deleted',
                extra={'image_task_id': image_task_id}
            )
            # Emit error event if we can determine the job_id from context
            # Note: Without ImageTask, we can't determine job_id, so we skip emit_event
            return
        
        job = image_task.job
        
        # Check if task or job was cancelled
        if image_task.status == ImageTask.Status.CANCELLED:
            logger.info(
                f'ImageTask {image_task_id} is cancelled - skipping execution',
                extra={'image_task_id': image_task_id, 'job_id': job.id}
            )
            return
        
        if job.status == Job.Status.CANCELLED:
            logger.info(
                f'Job {job.id} is cancelled - skipping ImageTask {image_task_id} execution',
                extra={'image_task_id': image_task_id, 'job_id': job.id}
            )
            # Mark task as cancelled if job is cancelled
            if image_task.status != ImageTask.Status.CANCELLED:
                image_task.status = ImageTask.Status.CANCELLED
                image_task.save(update_fields=['status', 'updated_at'])
            return
        
        # Check if task has a specific dataset_id (for multi-sheet Excel support)
        dataset_id = image_task.params.get('_dataset_id')
        if dataset_id:
            try:
                dataset = Dataset.objects.get(id=dataset_id)
            except Dataset.DoesNotExist:
                logger.warning(f"Dataset {dataset_id} not found, falling back to job dataset")
                dataset = job.dataset
        else:
            dataset = job.dataset
        
        # Emit START event
        trace_id = image_task.trace_id or None
        emit_event(
            job_id=job.id,
            image_task_id=image_task_id,
            event_type='START',
            level='INFO',
            message=f'Starting image generation for {image_task.algorithm_key}',
            trace_id=trace_id,
            progress=0
        )
        
        # Get algorithm from registry
        registry = AlgorithmRegistry()
        algorithm = registry.get(image_task.algorithm_key, image_task.algorithm_version)
        
        if not algorithm:
            raise ValueError(
                f"Algorithm not found: {image_task.algorithm_key} v{image_task.algorithm_version}"
            )
        
        # Emit PROGRESS event
        emit_event(
            job_id=job.id,
            image_task_id=image_task_id,
            event_type='PROGRESS',
            level='INFO',
            message='Executing algorithm',
            trace_id=trace_id,
            progress=30
        )
        
        # Get visualization config from job
        from apps.algorithms.visualization import VisualizationConfig
        viz_config = VisualizationConfig.from_dict(job.visualization_config)
        
        # Execute algorithm (consumes Dataset with visualization config)
        result = algorithm.run(dataset, image_task.params, viz_config=viz_config)
        
        # Check cancellation again
        job.refresh_from_db()
        if job.status == Job.Status.CANCELLED:
            emit_event(
                job_id=job.id,
                image_task_id=image_task_id,
                event_type='ERROR',
                level='WARNING',
                message='Task cancelled during execution',
                trace_id=trace_id
            )
            return
        
        # Emit PROGRESS event
        emit_event(
            job_id=job.id,
            image_task_id=image_task_id,
            event_type='PROGRESS',
            level='INFO',
            message='Saving artifacts',
            trace_id=trace_id,
            progress=70
        )
        
        # Save artifacts using FileField (handles storage automatically)
        if result.png_bytes and image_task.output_format in ['png', 'both']:
            image_task.artifact_png.save(
                f'job_{job.id}_task_{image_task_id}.png',
                ContentFile(result.png_bytes),
                save=False
            )
        
        if result.svg_text and image_task.output_format in ['svg', 'both']:
            image_task.artifact_svg.save(
                f'job_{job.id}_task_{image_task_id}.svg',
                ContentFile(result.svg_text.encode('utf-8')),
                save=False
            )
        
        # Save chart_data and update status
        image_task.chart_data = result.chart_data
        image_task.trace_id = trace_id
        image_task.save()
        
        # Emit DONE event
        emit_event(
            job_id=job.id,
            image_task_id=image_task_id,
            event_type='DONE',
            level='INFO',
            message='Image generation completed successfully',
            trace_id=trace_id,
            progress=100,
            payload={'chart_data_keys': list(result.chart_data.keys()) if result.chart_data else []}
        )
        
        # Check if all tasks are now complete and update job status
        # This handles the case of individual task retries
        _check_and_update_job_status(job)
        
    except Exception as e:
        # Log error to Django logger
        error_trace = traceback.format_exc()
        logger.error(
            f'Image generation failed for ImageTask {image_task_id}: {str(e)}',
            exc_info=True,
            extra={
                'image_task_id': image_task_id,
                'job_id': job.id if 'job' in locals() else None,
                'algorithm_key': image_task.algorithm_key if 'image_task' in locals() else None,
            }
        )
        
        # Emit ERROR event only if we have a job reference
        if 'job' in locals() and job:
            emit_event(
                job_id=job.id,
                image_task_id=image_task_id,
                event_type='ALGORITHM_ERROR',
                level='ERROR',
                message=f'Image generation failed: {str(e)}',
                trace_id=trace_id if 'trace_id' in locals() else None,
                payload={'error': str(e), 'trace': error_trace}
            )
            
            # Update ImageTask with error (don't raise to allow chord to complete)
            if 'image_task' in locals() and image_task:
                image_task.status = ImageTask.Status.FAILED
                image_task.error_code = 'ALGORITHM_ERROR'
                image_task.error_message = str(e)
                image_task.save()
                
                # Check if all tasks are now complete and update job status
                # This handles the case of individual task retries
                _check_and_update_job_status(job)
        
        # Don't raise - let chord complete so finalize_job can run
        # The error is already logged and ImageTask marked as FAILED (if it exists)


def run_job(job_id: int):
    """
    Run job - creates ImageTasks and enqueues them as a group.
    
    Args:
        job_id: Job ID
    """
    try:
        job = Job.objects.select_related('dataset').get(id=job_id)
        
        # Check cancellation
        if job.status == Job.Status.CANCELLED:
            return
        
        # Emit START event
        emit_event(
            job_id=job_id,
            event_type='START',
            level='INFO',
            message='Job started',
            progress=0
        )
        
        # Get ImageTasks for this job
        image_tasks = ImageTask.objects.filter(job=job, status=ImageTask.Status.PENDING)
        
        if not image_tasks.exists():
            emit_event(
                job_id=job_id,
                event_type='ERROR',
                level='WARNING',
                message='No pending image tasks found',
                progress=0
            )
            return
        
        # Create group of tasks
        task_signatures = [generate_image_task.s(task.id) for task in image_tasks]
        task_group = group(task_signatures)
        
        # Store task IDs in ImageTasks for cancellation support
        # Note: Celery doesn't provide task IDs before execution, so we'll check cancellation in the task itself
        
        # Create chord with callback using immutable signature
        chord_result = chord(task_group)(finalize_job.s(job_id))
        
        # Emit PROGRESS event with initial progress based on task count
        # Start at 0% since tasks haven't started yet
        emit_event(
            job_id=job_id,
            event_type='PROGRESS',
            level='INFO',
            message=f'Enqueued {image_tasks.count()} image tasks',
            progress=0
        )
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(
            f'Job execution failed for Job {job_id}: {str(e)}',
            exc_info=True,
            extra={'job_id': job_id}
        )
        
        emit_event(
            job_id=job_id,
            event_type='ERROR',
            level='ERROR',
            message=f'Job execution failed: {str(e)}',
            payload={'error': str(e), 'trace': error_trace}
        )
        
        if 'job' in locals():
            job.status = Job.Status.FAILED
            job.save()
        
        raise


@shared_task(bind=True, name='apps.jobs.tasks.finalize_job')
def finalize_job(self, task_results, job_id: int):
    """
    Finalize job after all ImageTasks complete.
    Calculates final status (SUCCESS, PARTIAL_SUCCESS, FAILED) and progress_total.
    
    Args:
        task_results: Results from chord (list of task results) - passed first by Celery
        job_id: Job ID - passed via immutable signature
    """
    try:
        job = Job.objects.get(id=job_id)
        
        # Get all ImageTasks for this job
        image_tasks = ImageTask.objects.filter(job=job)
        
        if not image_tasks.exists():
            job.status = Job.Status.FAILED
            job.progress_total = 0
            job.save()
            emit_event(
                job_id=job_id,
                event_type='ERROR',
                level='ERROR',
                message='No image tasks found',
                progress=0
            )
            return
        
        # Count statuses
        success_count = image_tasks.filter(status=ImageTask.Status.SUCCESS).count()
        failed_count = image_tasks.filter(status=ImageTask.Status.FAILED).count()
        cancelled_count = image_tasks.filter(status=ImageTask.Status.CANCELLED).count()
        total_count = image_tasks.count()
        completed_count = success_count + failed_count + cancelled_count
        
        # Calculate final status
        if success_count == total_count:
            job.status = Job.Status.SUCCESS
        elif success_count > 0 and failed_count > 0:
            job.status = Job.Status.PARTIAL_SUCCESS
        else:
            job.status = Job.Status.FAILED
        
        # Set progress_total: 100 if all tasks completed, otherwise average
        # When finalize_job runs, all tasks should be complete, so set to 100
        if total_count > 0:
            if completed_count == total_count:
                # All tasks have completed (success/failed/cancelled), so job is 100% complete
                job.progress_total = 100
            else:
                # Some tasks still pending/running (shouldn't happen, but handle gracefully)
                avg_progress = sum(task.progress for task in image_tasks) / total_count
                job.progress_total = int(avg_progress)
        else:
            job.progress_total = 0
        
        job.save()
        
        # Emit job_status_changed event for frontend detection
        emit_event(
            job_id=job_id,
            event_type='job_status_changed',
            level='INFO',
            message=f'Job status changed to {job.status}',
            progress=job.progress_total,
            payload={'status': job.status}
        )
        
        # Emit DONE event
        emit_event(
            job_id=job_id,
            event_type='DONE',
            level='INFO',
            message=f'Job completed: {job.status} ({success_count}/{total_count} successful)',
            progress=job.progress_total,
            payload={
                'success_count': success_count,
                'failed_count': failed_count,
                'total_count': total_count
            }
        )
        
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(
            f'Job finalization failed for Job {job_id}: {str(e)}',
            exc_info=True,
            extra={'job_id': job_id}
        )
        
        emit_event(
            job_id=job_id,
            event_type='ERROR',
            level='ERROR',
            message=f'Job finalization failed: {str(e)}',
            payload={'error': str(e), 'trace': error_trace}
        )
        
        if 'job' in locals():
            job.status = Job.Status.FAILED
            job.save()
        
        raise

