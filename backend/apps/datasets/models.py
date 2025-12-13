"""
Dataset model - canonical internal format for all data sources.
"""
from django.db import models
from django.core.validators import MinValueValidator


class Dataset(models.Model):
    """
    Canonical dataset model.
    All algorithms consume this model, never raw data.
    """
    SOURCE_TYPE_CHOICES = [
        ('lens', 'Lens API'),
        ('espacenet_excel', 'Espacenet Excel'),
        ('custom', 'Custom'),
    ]
    
    NORMALIZED_FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('parquet', 'Parquet'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPE_CHOICES,
        help_text="Source of the data (lens, espacenet_excel, custom)"
    )
    schema_version = models.CharField(
        max_length=20,
        default='v1',
        help_text="Schema version for compatibility"
    )
    normalized_format = models.CharField(
        max_length=20,
        choices=NORMALIZED_FORMAT_CHOICES,
        help_text="Format of normalized data (json or parquet)"
    )
    storage_path = models.CharField(
        max_length=500,
        help_text="Path to the normalized data file (relative to MEDIA_ROOT or absolute)"
    )
    summary_stats = models.JSONField(
        default=dict,
        help_text="Summary statistics (rows, columns, fields available)"
    )
    columns_map = models.JSONField(
        default=dict,
        help_text="Mapping of original columns to normalized columns"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'datasets_dataset'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Dataset {self.id} ({self.source_type}, {self.normalized_format})"

