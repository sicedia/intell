"""
Celery tasks for AI description generation.
"""
from celery import shared_task
from pathlib import Path
import json
import logging
from django.conf import settings
from apps.jobs.models import DescriptionTask, ImageTask, Job
from apps.ai_descriptions.providers import AIProviderRouter
from apps.audit.helpers import emit_event
import traceback

logger = logging.getLogger(__name__)


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
            'image_task', 'image_task__job', 'image_task__created_by', 'image_task__job__created_by'
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
        
        # Load dataset content for context
        dataset_content = None
        try:
            if job.dataset:
                dataset = job.dataset
                # Determine file path
                if dataset.storage_path.startswith('/') or ':' in dataset.storage_path:
                    # Absolute path
                    file_path = Path(dataset.storage_path)
                else:
                    # Relative to MEDIA_ROOT
                    file_path = Path(settings.MEDIA_ROOT) / dataset.storage_path
                
                # Read dataset JSON file
                if file_path.exists() and file_path.suffix == '.json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        dataset_data = json.load(f)
                        # Convert to string representation (truncate if too large)
                        dataset_content = json.dumps(dataset_data, ensure_ascii=False, indent=2)
                        logger.info(f"Loaded dataset from {file_path} ({len(dataset_content)} chars)")
                else:
                    logger.warning(f"Dataset file not found or not JSON: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to load dataset content: {e}")
            # Continue without dataset content - it's optional
            dataset_content = None
        
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
        
        # Update task progress
        description_task.progress = 30
        description_task.save(update_fields=['progress'])
        
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
        
        # Get preferences from description_task if stored
        provider_preference = None
        model_preference = None
        if description_task.prompt_snapshot and isinstance(description_task.prompt_snapshot, dict):
            provider_preference = description_task.prompt_snapshot.get('provider_preference')
            model_preference = description_task.prompt_snapshot.get('model_preference')
        
        # Get additional context for enriched prompt
        algorithm_key = image_task.algorithm_key
        source_type = job.dataset.source_type if job.dataset else None
        visualization_type = chart_data.get('type')
        
        # Emit PROGRESS event (processing)
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='PROGRESS',
            level='INFO',
            message='Processing with AI provider',
            trace_id=trace_id,
            progress=60
        )
        
        # Update task progress
        description_task.progress = 60
        description_task.save(update_fields=['progress'])
        
        # Use router to generate description with event callbacks
        from apps.ai_descriptions.providers import LITELLM_MODELS
        router = AIProviderRouter()
        
        # Define event callbacks for real-time feedback
        def on_model_attempt(model_name: str):
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='MODEL_ATTEMPT',
                level='INFO',
                message=f'Attempting model: {model_name}',
                trace_id=trace_id,
                payload={'model': model_name}
            )
        
        def on_model_failed(model_name: str, error: str):
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='MODEL_FAILED',
                level='WARNING',
                message=f'Model {model_name} failed: {error}',
                trace_id=trace_id,
                payload={'model': model_name, 'error': error}
            )
        
        def on_model_success(model_name: str):
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='MODEL_SUCCESS',
                level='INFO',
                message=f'Model {model_name} succeeded',
                trace_id=trace_id,
                payload={'model': model_name}
            )
        
        def on_fallback(from_model: str, to_model: str):
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='FALLBACK',
                level='INFO',
                message=f'Falling back from {from_model} to {to_model}',
                trace_id=trace_id,
                payload={'from_model': from_model, 'to_model': to_model}
            )
        
        try:
            result_text, model_used = router.generate_description(
                chart_data=chart_data,
                user_context=description_task.user_context,
                timeout=30,
                max_retries=3,
                provider_preference=provider_preference,
                model_preference=model_preference,
                algorithm_key=algorithm_key,
                source_type=source_type,
                visualization_type=visualization_type,
                dataset_content=dataset_content,
                on_model_attempt=on_model_attempt,
                on_model_failed=on_model_failed,
                on_model_success=on_model_success,
                on_fallback=on_fallback
            )
            # Determine provider based on model name
            # All models from LiteLLM should be in LITELLM_MODELS list
            if model_used in LITELLM_MODELS:
                provider_used = 'litellm'
            elif model_used == 'mock':
                provider_used = 'mock'
            else:
                # Fallback: if model name doesn't match known models, use 'litellm' as default
                provider_used = 'litellm'
        except Exception as e:
            # Enhanced error handling - capture which models failed
            error_message = str(e)
            logger.error(f"AI description generation failed: {error_message}")
            
            # Emit error event with details
            emit_event(
                job_id=job.id,
                description_task_id=description_task_id,
                event_type='AI_PROVIDER_ERROR',
                level='ERROR',
                message=f'AI description generation failed: {error_message}',
                trace_id=trace_id,
                payload={'error': error_message, 'failed_models': error_message}
            )
            
            # Update DescriptionTask with error
            description_task.status = DescriptionTask.Status.FAILED
            description_task.error_code = 'AI_PROVIDER_ERROR'
            description_task.error_message = error_message
            description_task.save()
            
            raise
        
        # Emit PROGRESS event (finalizing)
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='PROGRESS',
            level='INFO',
            message='Finalizing description',
            trace_id=trace_id,
            progress=90
        )
        
        # Update task progress
        description_task.progress = 90
        description_task.save(update_fields=['progress'])
        
        # model_used is already set from router.generate_description return value
        
        # Build prompt snapshot (preserve preferences if they were set)
        prompt_snapshot = {
            "chart_data_keys": list(chart_data.keys()) if chart_data else [],
            "user_context": description_task.user_context,
            "provider": provider_used,
            "model": model_used,
            "provider_preference_used": provider_preference,
            "model_preference_used": model_preference,
            "dataset_loaded": dataset_content is not None,
            "dataset_size": len(dataset_content) if dataset_content else 0
        }
        
        # Update DescriptionTask
        description_task.result_text = result_text
        description_task.provider_used = provider_used
        description_task.model_used = model_used  # This is the actual model name from LiteLLM
        description_task.prompt_snapshot = prompt_snapshot
        description_task.trace_id = trace_id
        description_task.status = DescriptionTask.Status.SUCCESS
        description_task.progress = 100
        # Explicitly save all fields to ensure model_used is persisted
        description_task.save(update_fields=[
            'result_text', 'provider_used', 'model_used', 'prompt_snapshot', 
            'trace_id', 'status', 'progress', 'updated_at'
        ])
        
        # Log the model used for debugging
        logger.info(f"Description task {description_task_id} completed successfully with model: {model_used}, provider: {provider_used}")
        # Verify it was saved correctly
        description_task.refresh_from_db()
        logger.info(f"Description task {description_task_id} after save - model_used: {description_task.model_used}, provider_used: {description_task.provider_used}")
        
        # Save the context used for AI description in ImageTask metadata
        if description_task.user_context:
            image_task.ai_context = description_task.user_context
            image_task.save(update_fields=['ai_context'])
        
        # Note: Notifications are created when the entire Job completes, not for individual descriptions
        # This reduces notification spam when processing multiple images in a batch
        
        # Emit DONE event
        emit_event(
            job_id=job.id,
            description_task_id=description_task_id,
            event_type='DONE',
            level='INFO',
            message='AI description generated successfully',
            trace_id=trace_id,
            progress=100,
            payload={'provider': provider_used, 'model': model_used, 'dataset_loaded': dataset_content is not None}
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
            
            # Note: Error notifications are created when the entire Job completes with errors,
            # not for individual description failures, to reduce notification spam
        
        raise

