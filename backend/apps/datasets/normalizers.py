"""
Dataset normalization functions.
Converts raw data from various sources into canonical Dataset format.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from django.conf import settings
from .models import Dataset


# Mapping of algorithm_key to required Excel sheet name
ALGORITHM_SHEET_MAPPING = {
    # Time series algorithms - use publication date sheet
    'patent_evolution': 'Earliest publication date (fam',
    'patent_cumulative': 'Earliest publication date (fam',
    'patent_trends_cumulative': 'Earliest publication date (fam',
    'patent_forecast': 'Earliest publication date (fam',
    # Ranking algorithms
    'top_patent_applicants': 'Applicants',
    'top_patent_inventors': 'Inventors',
    'top_patent_countries': 'Countries (family)',
    # Classification algorithms
    'cpc_treemap': 'CPC subgroups',
}


def get_sheet_for_algorithm(algorithm_key: str) -> str:
    """
    Get the required Excel sheet name for an algorithm.
    
    Args:
        algorithm_key: Algorithm identifier
        
    Returns:
        Sheet name to use
    """
    return ALGORITHM_SHEET_MAPPING.get(algorithm_key, 'Countries (family)')


def find_matching_sheet(excel_file: pd.ExcelFile, target_sheet: str) -> Optional[str]:
    """
    Find a sheet in the Excel file that matches the target (partial match).
    
    Args:
        excel_file: pandas ExcelFile object
        target_sheet: Target sheet name (can be partial)
        
    Returns:
        Matching sheet name or None
    """
    for sheet_name in excel_file.sheet_names:
        if target_sheet.lower() in sheet_name.lower():
            return sheet_name
    return None


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


def normalize_from_excel(file_path: str, sheet_name: str = "Countries (family)", algorithm_key: str = None) -> Dataset:
    """
    Convenience function to normalize from Excel file.
    
    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name to read (can be partial match)
        algorithm_key: If provided, automatically determines the correct sheet
        
    Returns:
        Dataset instance
    """
    # If algorithm_key is provided, get the required sheet
    if algorithm_key:
        sheet_name = get_sheet_for_algorithm(algorithm_key)
    
    # Open Excel file to find matching sheet
    try:
        excel_file = pd.ExcelFile(file_path)
        
        # Find matching sheet (supports partial matches)
        matching_sheet = find_matching_sheet(excel_file, sheet_name)
        
        if not matching_sheet:
            available_sheets = excel_file.sheet_names
            raise ValueError(
                f"No se encontró la hoja '{sheet_name}' en el archivo Excel. "
                f"Hojas disponibles: {available_sheets}. "
                f"Por favor, verifique que el archivo Excel sea un export válido de Espacenet."
            )
        
        # Read the data from the matched sheet
        df = pd.read_excel(excel_file, sheet_name=matching_sheet)
        raw_data = df.to_dict('records')
        
    except FileNotFoundError:
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    except ValueError:
        raise  # Re-raise ValueError for sheet not found
    except Exception as e:
        raise Exception(f"Error al leer el archivo Excel: {e}")
    
    return normalize("espacenet_excel", raw_data, file_path=file_path)

