"""
Pytest fixtures for jobs app tests.
"""
import pytest
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.datasets.models import Dataset


@pytest.fixture
def dataset_factory(db):
    """Factory to create Dataset instances."""
    def _create_dataset(**kwargs):
        defaults = {
            'source_type': 'espacenet_excel',
            'schema_version': 'v1',
            'normalized_format': 'json',
            'storage_path': 'datasets/test.json',
            'summary_stats': {'total_rows': 0, 'total_columns': 0},
            'columns_map': {}
        }
        defaults.update(kwargs)
        return Dataset.objects.create(**defaults)
    
    return _create_dataset


@pytest.fixture
def job_factory(db, dataset_factory):
    """Factory to create Job instances."""
    def _create_job(dataset=None, **kwargs):
        if dataset is None:
            dataset = dataset_factory()
        
        defaults = {
            'status': Job.Status.PENDING,
            'progress_total': 0,
        }
        defaults.update(kwargs)
        
        return Job.objects.create(dataset=dataset, **defaults)
    
    return _create_job


@pytest.fixture
def image_task_factory(db, job_factory):
    """Factory to create ImageTask instances."""
    def _create_image_task(job=None, **kwargs):
        if job is None:
            job = job_factory()
        
        defaults = {
            'algorithm_key': 'top_patent_countries',
            'algorithm_version': '1.0',
            'params': {'top_n': 10},
            'output_format': ImageTask.OutputFormat.BOTH,
            'status': ImageTask.Status.PENDING,
            'progress': 0,
        }
        defaults.update(kwargs)
        
        return ImageTask.objects.create(job=job, **defaults)
    
    return _create_image_task


@pytest.fixture
def description_task_factory(db, image_task_factory):
    """Factory to create DescriptionTask instances."""
    def _create_description_task(image_task=None, **kwargs):
        if image_task is None:
            image_task = image_task_factory(status=ImageTask.Status.SUCCESS)
        
        defaults = {
            'status': DescriptionTask.Status.PENDING,
            'progress': 0,
            'user_context': 'Test context',
        }
        defaults.update(kwargs)
        
        return DescriptionTask.objects.create(image_task=image_task, **defaults)
    
    return _create_description_task

