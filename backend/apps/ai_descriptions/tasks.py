"""
Celery tasks for AI description generation.
"""
from celery import shared_task
from apps.jobs.models import DescriptionTask, ImageTask, Job
from apps.ai_descriptions.providers import AIProviderRouter
from apps.audit.helpers import emit_event
import traceback


@shared_task(bind=True, name='apps.ai_descriptions.tasks.generate_description_task')
def generate_description_task(self, description_task_id: int):
    """
    Generate AI description for a chart.
    
    Args:
        description_task_id: DescriptionTask ID
    """
    try:
        # Get DescriptionTask and ImageTask
        description_task = DescriptionTask.objects.select_related(
            'image_task', 'image_task__job'
        ).get(id=description_task_id)
        image_task = description_task.image_task
        job = image_task.job
        
        # Check cancellation
        if job.status == Job.Status.CANCELLED:
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='ERROR',
                level='WARNING',
                message='Task cancelled',
                trace_id=description_task.trace_id
            )
            return
        
        # Emit START event
        trace_id = description_task.trace_id or None
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='START',
            level='INFO',
            message='Starting AI description generation',
            trace_id=trace_id,
            progress=0
        )
        
        # Get chart_data from ImageTask
        if not image_task.chart_data:
            raise ValueError("ImageTask has no chart_data")
        
        chart_data = image_task.chart_data
        
        # Emit PROGRESS event
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='PROGRESS',
            level='INFO',
            message='Calling AI provider',
            trace_id=trace_id,
            progress=30
        )
        
        # Check cancellation again
        job.refresh_from_db()
        if job.status == Job.Status.CANCELLED:
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='ERROR',
                level='WARNING',
                message='Task cancelled during execution',
                trace_id=trace_id
            )
            return
        
        # Get provider_preference from description_task if stored
        provider_preference = None
        if description_task.prompt_snapshot and isinstance(description_task.prompt_snapshot, dict):
            provider_preference = description_task.prompt_snapshot.get('provider_preference')
        
        # Use router to generate description
        router = AIProviderRouter()
        result_text, provider_used = router.generate_description(
            chart_data=chart_data,
            user_context=description_task.user_context,
            timeout=30,
            max_retries=3,
            provider_preference=provider_preference
        )
        
        # Determine model_used (simplified for MVP)
        model_used = "gpt-4" if provider_used == "openai" else \
                    "claude-3-opus" if provider_used == "anthropic" else \
                    "mock"
        
        # Build prompt snapshot (preserve provider_preference if it was set)
        prompt_snapshot = {
            "chart_data_keys": list(chart_data.keys()) if chart_data else [],
            "user_context": description_task.user_context,
            "provider": provider_used,
            "provider_preference_used": provider_preference
        }
        
        # Update DescriptionTask
        description_task.result_text = result_text
        description_task.provider_used = provider_used
        description_task.model_used = model_used
        description_task.prompt_snapshot = prompt_snapshot
        description_task.trace_id = trace_id
        description_task.save()
        
        # Emit DONE event
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='DONE',
            level='INFO',
            message='AI description generated successfully',
            trace_id=trace_id,
            progress=100,
            payload={'provider': provider_used, 'model': model_used}
        )
        
    except Exception as e:
        # Emit ERROR event
        error_trace = traceback.format_exc()
        emit_event(
            job_id=job.id if 'job' in locals() else None,
            description_task_id=description_task_id,
            event_type='AI_PROVIDER_ERROR',
            level='ERROR',
            message=f'AI description generation failed: {str(e)}',
            trace_id=trace_id if 'trace_id' in locals() else None,
            payload={'error': str(e), 'trace': error_trace}
        )
        
        # Update DescriptionTask with error
        if 'description_task' in locals():
            description_task.status = DescriptionTask.Status.FAILED
            description_task.error_code = 'AI_PROVIDER_ERROR'
            description_task.error_message = str(e)
            description_task.save()
        
        raise

