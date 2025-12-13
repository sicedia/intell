"""
Pytest configuration and fixtures for integration tests.
"""
import pytest
from pathlib import Path
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
import json

from apps.datasets.models import Dataset
from apps.jobs.models import Job, ImageTask, DescriptionTask
from apps.algorithms.registry import AlgorithmRegistry
from apps.algorithms.demo.top_patent_countries import TopPatentCountriesAlgorithm


# django_db_setup is provided by pytest-django
# Migrations are run automatically by pytest-django


@pytest.fixture
def excel_test_file():
    """Path to test Excel file."""
    # Try excels folder first
    excel_path = Path(__file__).parent.parent / 'context' / 'excels' / 'Filters_20250522_1212.xlsx'
    if not excel_path.exists():
        # Fallback to context folder
        excel_path = Path(__file__).parent.parent / 'context' / 'Filters_20250522_1212.xlsx'
    if not excel_path.exists():
        # Try other file
        excel_path = Path(__file__).parent.parent / 'context' / 'excels' / 'Filters_20250331_1141.xlsx'
    if not excel_path.exists():
        pytest.skip(f"Test Excel file not found")
    return excel_path


@pytest.fixture
def dataset_mock(db):
    """Create a mock Dataset for testing."""
    # Create a minimal normalized dataset JSON
    test_data = {
        "data": [
            {"country": "US", "count": 100},
            {"country": "CN", "count": 80},
            {"country": "JP", "count": 60},
        ],
        "metadata": {
            "source": "test",
            "total_rows": 3
        }
    }
    
    # Save to MEDIA_ROOT
    media_root = Path(settings.MEDIA_ROOT)
    media_root.mkdir(parents=True, exist_ok=True)
    datasets_dir = media_root / 'datasets'
    datasets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a unique filename
    import uuid
    filename = f"test_dataset_{uuid.uuid4().hex[:8]}.json"
    file_path = datasets_dir / filename
    
    # Write JSON file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(test_data, f)
    
    # Create Dataset instance
    dataset = Dataset.objects.create(
        source_type='espacenet_excel',
        schema_version='v1',
        normalized_format='json',
        storage_path=f'datasets/{filename}',
        summary_stats={
            'total_rows': 3,
            'total_columns': 2,
            'columns': ['country', 'count']
        },
        columns_map={
            'country': 'country',
            'count': 'count'
        }
    )
    
    yield dataset
    
    # Cleanup: delete file and dataset
    if file_path.exists():
        file_path.unlink()
    dataset.delete()


@pytest.fixture
def algorithm_registry():
    """Register demo algorithm for testing."""
    registry = AlgorithmRegistry()
    registry.register("top_patent_countries", "1.0", TopPatentCountriesAlgorithm())
    return registry


@pytest.fixture
def job_factory(db):
    """Factory function to create Job instances."""
    def _create_job(dataset=None, **kwargs):
        if dataset is None:
            # Create a minimal dataset if not provided
            from apps.datasets.models import Dataset
            dataset = Dataset.objects.create(
                source_type='espacenet_excel',
                schema_version='v1',
                normalized_format='json',
                storage_path='datasets/test.json',
                summary_stats={'total_rows': 0, 'total_columns': 0},
                columns_map={}
            )
        
        defaults = {
            'status': Job.Status.PENDING,
            'progress_total': 0,
        }
        defaults.update(kwargs)
        
        return Job.objects.create(dataset=dataset, **defaults)
    
    return _create_job


@pytest.fixture
def image_task_factory(db):
    """Factory function to create ImageTask instances."""
    def _create_image_task(job=None, **kwargs):
        if job is None:
            # Create a job if not provided
            from apps.datasets.models import Dataset
            dataset = Dataset.objects.create(
                source_type='espacenet_excel',
                schema_version='v1',
                normalized_format='json',
                storage_path='datasets/test.json',
                summary_stats={'total_rows': 0, 'total_columns': 0},
                columns_map={}
            )
            job = Job.objects.create(dataset=dataset, status=Job.Status.PENDING)
        
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
def description_task_factory(db):
    """Factory function to create DescriptionTask instances."""
    def _create_description_task(image_task=None, **kwargs):
        if image_task is None:
            # Create image_task if not provided
            from apps.datasets.models import Dataset
            dataset = Dataset.objects.create(
                source_type='espacenet_excel',
                schema_version='v1',
                normalized_format='json',
                storage_path='datasets/test.json',
                summary_stats={'total_rows': 0, 'total_columns': 0},
                columns_map={}
            )
            job = Job.objects.create(dataset=dataset, status=Job.Status.PENDING)
            image_task = ImageTask.objects.create(
                job=job,
                algorithm_key='top_patent_countries',
                algorithm_version='1.0',
                params={},
                output_format=ImageTask.OutputFormat.BOTH,
                status=ImageTask.Status.SUCCESS
            )
        
        defaults = {
            'status': DescriptionTask.Status.PENDING,
            'progress': 0,
            'user_context': 'Test context',
        }
        defaults.update(kwargs)
        
        return DescriptionTask.objects.create(image_task=image_task, **defaults)
    
    return _create_description_task

