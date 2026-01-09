"""
End-to-end test for job processing pipeline.
"""
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from pathlib import Path
import os

from apps.datasets.models import Dataset
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.algorithms.registry import AlgorithmRegistry
from apps.algorithms.demo.top_patent_countries import TopPatentCountriesAlgorithm
from apps.datasets.normalizers import normalize_from_excel
from apps.jobs.tasks import generate_image_task, finalize_job
from apps.ai_descriptions.tasks import generate_description_task


class JobPipelineTestCase(TestCase):
    """Test complete job processing pipeline."""
    
    def setUp(self):
        """Set up test data."""
        # Register algorithm
        registry = AlgorithmRegistry()
        registry.register("top_patent_countries", "1.0", TopPatentCountriesAlgorithm())
        
        # Path to test Excel file
        self.excel_path = Path(__file__).parent.parent.parent.parent / 'context' / 'excels' / 'Filters_20250522_1212.xlsx'
        if not self.excel_path.exists():
            # Fallback path
            self.excel_path = Path(__file__).parent.parent.parent.parent / 'context' / 'Filters_20250522_1212.xlsx'
    
    def test_end_to_end_pipeline(self):
        """Test complete pipeline: Excel → Dataset → Job → ImageTask → DescriptionTask."""
        # Skip if Excel file doesn't exist
        if not self.excel_path.exists():
            self.skipTest(f"Test Excel file not found: {self.excel_path}")
        
        # Step 1: Create Dataset from Excel
        dataset = normalize_from_excel(str(self.excel_path))
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.source_type, 'espacenet_excel')
        self.assertEqual(dataset.normalized_format, 'json')
        self.assertIsNotNone(dataset.storage_path)
        
        # Verify file exists
        file_path = Path(settings.MEDIA_ROOT) / dataset.storage_path
        self.assertTrue(file_path.exists(), f"Dataset file should exist: {file_path}")
        
        # Verify summary_stats
        self.assertIn('total_rows', dataset.summary_stats)
        self.assertIn('total_columns', dataset.summary_stats)
        
        # Step 2: Create Job with ImageTask
        job = Job.objects.create(
            dataset=dataset,
            status=Job.Status.PENDING
        )
        
        image_task = ImageTask.objects.create(
            job=job,
            algorithm_key="top_patent_countries",
            algorithm_version="1.0",
            params={"top_n": 15},
            output_format=ImageTask.OutputFormat.BOTH,
            status=ImageTask.Status.PENDING
        )
        
        # Step 3: Execute generate_image_task (synchronously for test)
        try:
            generate_image_task(image_task.id)
        except Exception as e:
            self.fail(f"generate_image_task failed: {e}")
        
        # Refresh from DB
        image_task.refresh_from_db()
        job.refresh_from_db()
        
        # Verify ImageTask completed
        self.assertEqual(image_task.status, ImageTask.Status.SUCCESS)
        self.assertIsNotNone(image_task.chart_data)
        self.assertIn('type', image_task.chart_data)
        self.assertIn('series', image_task.chart_data)
        
        # Verify artifacts exist (if saved)
        # Note: In test, artifacts might be in memory, so we check chart_data instead
        
        # Step 4: Test finalize_job
        # finalize_job is a Celery task with bind=True, so self is passed automatically
        # When calling directly, we need to pass (task_results, job_id)
        # We'll use .apply() to execute it synchronously
        finalize_job.apply(args=([], job.id))
        job.refresh_from_db()
        
        # Verify job status
        self.assertIn(job.status, [Job.Status.SUCCESS, Job.Status.PARTIAL_SUCCESS])
        self.assertGreaterEqual(job.progress_total, 0)
        self.assertLessEqual(job.progress_total, 100)
        
        # Step 5: Create DescriptionTask
        description_task = DescriptionTask.objects.create(
            image_task=image_task,
            user_context="Describe this chart",
            status=DescriptionTask.Status.PENDING
        )
        
        # Step 6: Execute generate_description_task (synchronously for test)
        try:
            generate_description_task(description_task.id)
        except Exception as e:
            self.fail(f"generate_description_task failed: {e}")
        
        # Refresh from DB
        description_task.refresh_from_db()
        
        # Verify DescriptionTask completed
        self.assertEqual(description_task.status, DescriptionTask.Status.SUCCESS)
        self.assertIsNotNone(description_task.result_text)
        self.assertIsNotNone(description_task.provider_used)
        
        # Verify EventLog has events
        from apps.audit.models import EventLog
        events = EventLog.objects.filter(job=job)
        self.assertGreater(events.count(), 0, "Should have event logs")
        
        # Verify chart_data structure
        self.assertIn('type', image_task.chart_data)
        self.assertIn('title', image_task.chart_data)
        self.assertIn('series', image_task.chart_data)
        if 'totals' in image_task.chart_data:
            self.assertIsInstance(image_task.chart_data['totals'], dict)
