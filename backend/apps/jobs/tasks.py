"""
Celery tasks for job orchestration.
"""
from celery import group, chord
from celery import shared_task
from django.core.files.base import ContentFile
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.algorithms.registry import AlgorithmRegistry
from apps.audit.helpers import emit_event
import traceback


@shared_task(bind=True, name='apps.jobs.tasks.generate_image_task')
def generate_image_task(self, image_task_id: int):
    """
    Generate chart image for an ImageTask.
    Consumes Dataset from Job.dataset.
    
    Args:
        image_task_id: ImageTask ID
    """
    try:
        # Get ImageTask and Job
        image_task = ImageTask.objects.select_related('job', 'job__dataset').get(id=image_task_id)
        job = image_task.job
        dataset = job.dataset
        
        # Check cancellation
        if job.status == Job.Status.CANCELLED:
            emit_event(
                job_id=job.id,
                image_task_id=image_task_id,
                event_type='ERROR',
                level='WARNING',
                message='Task cancelled',
                trace_id=image_task.trace_id
            )
            return
        
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
        
        # Execute algorithm (consumes Dataset)
        result = algorithm.run(dataset, image_task.params)
        
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
        
    except Exception as e:
        # Emit ERROR event
        error_trace = traceback.format_exc()
        emit_event(
            job_id=job.id if 'job' in locals() else None,
            image_task_id=image_task_id,
            event_type='ALGORITHM_ERROR',
            level='ERROR',
            message=f'Image generation failed: {str(e)}',
            trace_id=trace_id if 'trace_id' in locals() else None,
            payload={'error': str(e), 'trace': error_trace}
        )
        
        # Update ImageTask with error (don't raise to allow chord to complete)
        if 'image_task' in locals():
            image_task.status = ImageTask.Status.FAILED
            image_task.error_code = 'ALGORITHM_ERROR'
            image_task.error_message = str(e)
            image_task.save()
        
        # Don't raise - let chord complete so finalize_job can run
        # The error is already logged and ImageTask marked as FAILED


@shared_task(bind=True, name='apps.jobs.tasks.run_job')
def run_job(self, job_id: int):
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
        task_group = group(
            generate_image_task.s(task.id) for task in image_tasks
        )
        
        # Create chord with callback using immutable signature
        chord(task_group)(finalize_job.si(job_id))
        
        # Emit PROGRESS event
        emit_event(
            job_id=job_id,
            event_type='PROGRESS',
            level='INFO',
            message=f'Enqueued {image_tasks.count()} image tasks',
            progress=10
        )
        
    except Exception as e:
        error_trace = traceback.format_exc()
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
        total_count = image_tasks.count()
        
        # Calculate final status
        if success_count == total_count:
            job.status = Job.Status.SUCCESS
        elif success_count > 0 and failed_count > 0:
            job.status = Job.Status.PARTIAL_SUCCESS
        else:
            job.status = Job.Status.FAILED
        
        # Recalculate progress_total as average of ImageTask progress
        if total_count > 0:
            avg_progress = sum(task.progress for task in image_tasks) / total_count
            job.progress_total = int(avg_progress)
        else:
            job.progress_total = 0
        
        job.save()
        
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

