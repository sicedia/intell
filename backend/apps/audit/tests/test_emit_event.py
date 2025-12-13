"""
Tests for emit_event helper function.
"""
import pytest
from apps.audit.models import EventLog
from apps.audit.helpers import emit_event
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.datasets.models import Dataset


@pytest.mark.django_db
class TestEmitEvent:
    """Test emit_event helper function."""
    
    def test_emit_event_for_job(self):
        """Test emitting event for a Job."""
        # Create dataset and job
        dataset = Dataset.objects.create(
            source_type='espacenet_excel',
            schema_version='v1',
            normalized_format='json',
            storage_path='datasets/test.json',
            summary_stats={'total_rows': 0, 'total_columns': 0},
            columns_map={}
        )
        
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.PENDING,
            progress_total=0
        )
        
        # Emit event
        emit_event(
            job_id=job.id,
            event_type='START',
            level='INFO',
            message='Job started',
            progress=10
        )
        
        # Verify EventLog created
        events = EventLog.objects.filter(job=job)
        assert events.count() == 1
        
        event = events.first()
        assert event.event_type == 'START'
        assert event.level == 'INFO'
        assert event.message == 'Job started'
        assert event.job == job
        assert event.image_task is None
        assert event.description_task is None
        
        # Verify Job status/progress updated
        job.refresh_from_db()
        assert job.progress_total == 10
    
    def test_emit_event_for_image_task(self):
        """Test emitting event for an ImageTask."""
        # Create dataset, job, and image_task
        dataset = Dataset.objects.create(
            source_type='espacenet_excel',
            schema_version='v1',
            normalized_format='json',
            storage_path='datasets/test.json',
            summary_stats={'total_rows': 0, 'total_columns': 0},
            columns_map={}
        )
        
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.RUNNING,
            progress_total=0
        )
        
        image_task = ImageTask.objects.create(
            job=job,
            algorithm_key='test_algorithm',
            algorithm_version='1.0',
            params={},
            output_format=ImageTask.OutputFormat.BOTH,
            status=ImageTask.Status.PENDING,
            progress=0
        )
        
        # Emit event
        emit_event(
            job_id=job.id,
            image_task_id=image_task.id,
            event_type='PROGRESS',
            level='INFO',
            message='Processing image',
            progress=50
        )
        
        # Verify EventLog created
        events = EventLog.objects.filter(image_task=image_task)
        assert events.count() == 1
        
        event = events.first()
        assert event.event_type == 'PROGRESS'
        assert event.image_task == image_task
        assert event.job == job
        
        # Verify ImageTask updated
        image_task.refresh_from_db()
        assert image_task.progress == 50
    
    def test_emit_event_for_description_task(self):
        """Test emitting event for a DescriptionTask."""
        # Create full chain: dataset -> job -> image_task -> description_task
        dataset = Dataset.objects.create(
            source_type='espacenet_excel',
            schema_version='v1',
            normalized_format='json',
            storage_path='datasets/test.json',
            summary_stats={'total_rows': 0, 'total_columns': 0},
            columns_map={}
        )
        
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.RUNNING,
            progress_total=50
        )
        
        image_task = ImageTask.objects.create(
            job=job,
            algorithm_key='test_algorithm',
            algorithm_version='1.0',
            params={},
            output_format=ImageTask.OutputFormat.BOTH,
            status=ImageTask.Status.SUCCESS,
            progress=100
        )
        
        description_task = DescriptionTask.objects.create(
            image_task=image_task,
            status=DescriptionTask.Status.PENDING,
            progress=0,
            user_context='Test context'
        )
        
        # Emit event
        emit_event(
            job_id=job.id,
            image_task_id=image_task.id,
            description_task_id=description_task.id,
            event_type='START',
            level='INFO',
            message='Generating description',
            progress=25
        )
        
        # Verify EventLog created
        events = EventLog.objects.filter(description_task=description_task)
        assert events.count() == 1
        
        event = events.first()
        assert event.description_task == description_task
        assert event.image_task == image_task
        assert event.job == job
        
        # Verify DescriptionTask updated
        description_task.refresh_from_db()
        assert description_task.progress == 25
    
    def test_emit_event_with_error(self):
        """Test emitting error event."""
        dataset = Dataset.objects.create(
            source_type='espacenet_excel',
            schema_version='v1',
            normalized_format='json',
            storage_path='datasets/test.json',
            summary_stats={'total_rows': 0, 'total_columns': 0},
            columns_map={}
        )
        
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.RUNNING,
            progress_total=50
        )
        
        image_task = ImageTask.objects.create(
            job=job,
            algorithm_key='test_algorithm',
            algorithm_version='1.0',
            params={},
            output_format=ImageTask.OutputFormat.BOTH,
            status=ImageTask.Status.RUNNING,
            progress=50
        )
        
        # Emit error event
        emit_event(
            job_id=job.id,
            image_task_id=image_task.id,
            event_type='ERROR',
            level='ERROR',
            message='Algorithm failed',
            payload={'error_code': 'ALGORITHM_ERROR', 'error_message': 'Test error'}
        )
        
        # Verify EventLog created
        events = EventLog.objects.filter(event_type='ERROR')
        assert events.count() == 1
        
        event = events.first()
        assert event.level == 'ERROR'
        assert event.payload is not None
        assert event.payload['error_code'] == 'ALGORITHM_ERROR'
        
        # Verify ImageTask status updated to FAILED
        image_task.refresh_from_db()
        assert image_task.status == ImageTask.Status.FAILED
        
        # Verify error information is in the event payload
        event = events.first()
        assert event.payload is not None
        assert event.payload['error_code'] == 'ALGORITHM_ERROR'
    
    def test_emit_event_generates_trace_id(self):
        """Test that emit_event generates trace_id if not provided."""
        dataset = Dataset.objects.create(
            source_type='espacenet_excel',
            schema_version='v1',
            normalized_format='json',
            storage_path='datasets/test.json',
            summary_stats={'total_rows': 0, 'total_columns': 0},
            columns_map={}
        )
        
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.PENDING,
            progress_total=0
        )
        
        # Emit event without trace_id
        emit_event(
            job_id=job.id,
            event_type='START',
            level='INFO',
            message='Job started'
        )
        
        # Verify trace_id was generated
        event = EventLog.objects.filter(job=job).first()
        assert event.trace_id is not None
        assert len(event.trace_id) > 0

