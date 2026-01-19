"""
Dataset normalization functions.
Converts raw data from various sources into canonical Dataset format.
"""
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
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

# Expected sheet names for Espacenet Excel files (partial matches allowed)
# These are the main data sheets we expect in Espacenet exports
EXPECTED_ESPACENET_SHEETS = [
    'Countries (family)',
    'Countries',
    'Inventors',
    'Applicants',
    'Earliest publication date',
    'Earliest priority date',  # Also valid
    'CPC subgroups',
    'CPC main groups',  # Also valid
    'CPC',
    'IPC subgroups',  # Also valid
    'IPC main groups',  # Also valid
]

# Keywords for detecting numeric columns (Number of documents)
NUMERIC_COLUMN_KEYWORDS = [
    'number of documents',
    'number',
    'count',
    'documents',
    'publications',
    'patents',
    'cantidad',
    'documentos',
    'publicaciones',
]


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


def validate_espacenet_excel(file_path: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validate that an Excel file has the expected structure of an Espacenet export.
    
    Args:
        file_path: Path to Excel file
        
    Returns:
        Tuple of (is_valid, error_message, validation_details)
        validation_details contains:
        - found_sheets: List of found expected sheets
        - available_sheets: All sheet names in the file
        - sheet_validations: Dict mapping sheet names to their validation results
    """
    validation_details = {
        'found_sheets': [],
        'available_sheets': [],
        'sheet_validations': {},
    }
    
    # Use context manager to ensure file is closed
    try:
        with pd.ExcelFile(file_path) as excel_file:
            available_sheets = excel_file.sheet_names
            validation_details['available_sheets'] = available_sheets
            
            if not available_sheets:
                return False, "El archivo Excel no contiene hojas. Por favor, verifique que sea un archivo Excel válido.", validation_details
            
            # Check if at least one expected sheet exists
            found_expected_sheets = []
            for expected_sheet in EXPECTED_ESPACENET_SHEETS:
                matching = find_matching_sheet(excel_file, expected_sheet)
                if matching:
                    found_expected_sheets.append(matching)
            
            validation_details['found_sheets'] = found_expected_sheets
            
            if not found_expected_sheets:
                return (
                    False,
                    f"El archivo Excel no parece ser un export válido de Espacenet. "
                    f"No se encontraron hojas esperadas (Countries, Inventors, Applicants, Earliest publication date, CPC subgroups). "
                    f"Hojas disponibles: {', '.join(available_sheets)}. "
                    f"Por favor, verifique que el archivo sea un export de Espacenet.",
                    validation_details
                )
            
            # Validate each found sheet - we only need AT LEAST ONE valid sheet
            valid_sheets_count = 0
            sheet_errors = []
            sheet_warnings = []
            
            for sheet_name in found_expected_sheets:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    sheet_validation = {
                        'has_data': len(df) > 0,
                        'columns': list(df.columns),
                        'has_numeric_column': False,
                        'has_text_column': False,
                        'is_valid': False,
                        'errors': [],
                        'warnings': [],
                    }
                    
                    # Skip empty sheets (they're not invalid, just not useful)
                    if len(df) == 0:
                        sheet_validation['warnings'].append(f"La hoja '{sheet_name}' está vacía.")
                        sheet_warnings.append(f"Hoja '{sheet_name}': está vacía (se ignorará)")
                        validation_details['sheet_validations'][sheet_name] = sheet_validation
                        continue
                    
                    # Need at least 2 columns
                    if len(df.columns) < 2:
                        sheet_validation['errors'].append(
                            f"La hoja '{sheet_name}' debe tener al menos 2 columnas. "
                            f"Columnas encontradas: {list(df.columns)}"
                        )
                        validation_details['sheet_validations'][sheet_name] = sheet_validation
                        sheet_errors.append(f"Hoja '{sheet_name}': debe tener al menos 2 columnas")
                        continue
                    
                    # Check for numeric column - be more flexible
                    # First try to find by name (preferred)
                    has_numeric = False
                    numeric_col = None
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(keyword in col_lower for keyword in NUMERIC_COLUMN_KEYWORDS):
                            # Check if column actually contains numeric data
                            if pd.api.types.is_numeric_dtype(df[col]):
                                has_numeric = True
                                numeric_col = col
                                sheet_validation['has_numeric_column'] = True
                                break
                            elif df[col].dtype == 'object':
                                # Try to convert to numeric
                                numeric_values = pd.to_numeric(df[col], errors='coerce')
                                if not numeric_values.isna().all():
                                    has_numeric = True
                                    numeric_col = col
                                    sheet_validation['has_numeric_column'] = True
                                    break
                    
                    # If not found by name, try to find any numeric column
                    if not has_numeric:
                        for col in df.columns:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                # Check if it has meaningful numeric data (not all zeros or all same value)
                                if df[col].notna().any() and df[col].nunique() > 1:
                                    has_numeric = True
                                    numeric_col = col
                                    sheet_validation['has_numeric_column'] = True
                                    break
                            elif df[col].dtype == 'object':
                                # Try to convert to numeric
                                numeric_values = pd.to_numeric(df[col], errors='coerce')
                                if not numeric_values.isna().all() and numeric_values.nunique() > 1:
                                    has_numeric = True
                                    numeric_col = col
                                    sheet_validation['has_numeric_column'] = True
                                    break
                    
                    # Check for text column - be more flexible
                    has_text = False
                    text_col = None
                    for col in df.columns:
                        # Skip the numeric column we already found
                        if col == numeric_col:
                            continue
                        # Check if it's not numeric or if it's numeric but looks like text (years, codes, etc.)
                        if not pd.api.types.is_numeric_dtype(df[col]):
                            if df[col].notna().any():
                                has_text = True
                                text_col = col
                                sheet_validation['has_text_column'] = True
                                break
                        else:
                            # Even if numeric, if it's not the numeric column we're using, it could be text-like
                            # (e.g., years, country codes stored as numbers)
                            if df[col].notna().any():
                                has_text = True
                                text_col = col
                                sheet_validation['has_text_column'] = True
                                break
                    
                    # Validate this sheet
                    if has_numeric and has_text:
                        sheet_validation['is_valid'] = True
                        valid_sheets_count += 1
                    else:
                        if not has_numeric:
                            sheet_validation['errors'].append(
                                f"No se encontró una columna numérica válida. "
                                f"Columnas: {list(df.columns)}"
                            )
                        if not has_text:
                            sheet_validation['errors'].append(
                                f"No se encontró una columna de texto válida. "
                                f"Columnas: {list(df.columns)}"
                            )
                    
                    validation_details['sheet_validations'][sheet_name] = sheet_validation
                    
                    if sheet_validation['errors']:
                        sheet_errors.extend([f"Hoja '{sheet_name}': {err}" for err in sheet_validation['errors']])
                    
                except Exception as e:
                    sheet_validation = {
                        'has_data': False,
                        'columns': [],
                        'has_numeric_column': False,
                        'has_text_column': False,
                        'is_valid': False,
                        'errors': [f"Error al leer la hoja: {str(e)}"],
                        'warnings': [],
                    }
                    validation_details['sheet_validations'][sheet_name] = sheet_validation
                    sheet_errors.append(f"Hoja '{sheet_name}': Error al leer - {str(e)}")
            
            # We only need AT LEAST ONE valid sheet to consider the file valid
            if valid_sheets_count == 0:
                error_msg = (
                    f"El archivo Excel no tiene la estructura esperada de Espacenet. "
                    f"No se encontró ninguna hoja válida con datos procesables.\n\n"
                )
                if sheet_errors:
                    error_msg += "Errores encontrados:\n" + "\n".join(f"- {err}" for err in sheet_errors)
                if sheet_warnings:
                    error_msg += "\n\nAdvertencias:\n" + "\n".join(f"- {warn}" for warn in sheet_warnings)
                error_msg += "\n\nPor favor, verifique que el archivo sea un export válido de Espacenet."
                return False, error_msg, validation_details
            
            return True, "", validation_details
        
    except FileNotFoundError:
        return False, f"Archivo no encontrado o no se pudo leer: {file_path}", validation_details
    except Exception as e:
        return False, f"Error al validar el archivo Excel: {str(e)}", validation_details


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

