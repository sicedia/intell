# Datasets App

Canonical dataset normalization and management. All algorithms consume `Dataset` instances, never raw data.

## Modules

### `models.py`
- `Dataset`: Canonical dataset model
  - Fields: `source_type`, `schema_version`, `normalized_format`, `storage_path`, `summary_stats`, `columns_map`
  - All algorithms must consume this model
  - File must exist physically on disk

### `normalizers.py`
Functions to normalize raw data into canonical `Dataset` format:
- `normalize(source_type, raw_data) -> Dataset`: Main normalization function
  - Converts raw data to DataFrame
  - Calculates summary statistics
  - Creates columns mapping
  - Persists Dataset with file on disk
  - Returns Dataset instance
- `normalize_from_excel(file_path, sheet_name) -> Dataset`: Convenience function for Excel files

## Usage

Normalize data:
```python
from apps.datasets.normalizers import normalize, normalize_from_excel

# From Excel
dataset = normalize_from_excel("path/to/file.xlsx")

# From raw data
from apps.ingestion.connectors import EspacenetExcelParser
parser = EspacenetExcelParser()
raw_data = parser.parse("path/to/file.xlsx")
dataset = normalize("espacenet_excel", raw_data)
```

Access dataset:
```python
# Dataset file exists at MEDIA_ROOT / dataset.storage_path
# Read data: load JSON/Parquet from storage_path
# summary_stats contains: total_rows, total_columns, columns, data_types, null_counts
```

