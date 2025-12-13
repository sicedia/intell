"""
Dataset normalization functions.
Converts raw data from various sources into canonical Dataset format.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from django.conf import settings
from .models import Dataset


def normalize(source_type: str, raw_data: List[Dict[str, Any]], **kwargs) -> Dataset:
    """
    Normalize raw data into canonical Dataset format.
    
    Args:
        source_type: Type of source (lens, espacenet_excel, custom)
        raw_data: List of dictionaries with raw data
        **kwargs: Additional parameters (e.g., file_path for Excel)
        
    Returns:
        Dataset instance with normalized data persisted
    """
    # Convert raw data to DataFrame for processing
    df = pd.DataFrame(raw_data)
    
    # Calculate summary statistics
    summary_stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
    }
    
    # Create columns map (identity mapping for now, can be customized)
    columns_map = {col: col for col in df.columns}
    
    # Determine normalized format (JSON for MVP)
    normalized_format = 'json'
    
    # Save normalized data to file
    dataset_dir = Path(settings.MEDIA_ROOT) / 'datasets'
    dataset_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    import uuid
    filename = f"{source_type}_{uuid.uuid4().hex[:8]}.json"
    file_path = dataset_dir / filename
    
    # Save as JSON
    df.to_json(file_path, orient='records', date_format='iso', indent=2)
    
    # Get relative path from MEDIA_ROOT
    storage_path = str(file_path.relative_to(settings.MEDIA_ROOT))
    
    # Create Dataset instance
    dataset = Dataset.objects.create(
        source_type=source_type,
        schema_version='v1',
        normalized_format=normalized_format,
        storage_path=storage_path,
        summary_stats=summary_stats,
        columns_map=columns_map,
    )
    
    # Verify file exists
    if not file_path.exists():
        raise Exception(f"Failed to create dataset file: {file_path}")
    
    return dataset


def normalize_from_excel(file_path: str, sheet_name: str = "Countries (family)") -> Dataset:
    """
    Convenience function to normalize from Excel file.
    
    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name to read
        
    Returns:
        Dataset instance
    """
    from apps.ingestion.connectors import EspacenetExcelParser
    
    parser = EspacenetExcelParser()
    raw_data = parser.parse(file_path, sheet_name=sheet_name)
    
    return normalize("espacenet_excel", raw_data, file_path=file_path)

