# Ingestion App

Data source connectors for ingesting raw data from various sources.

## Modules

### `connectors.py`
Connectors for different data sources:
- `LensConnector`: Connector for Lens API
  - Currently implements mock for MVP
  - Prepared for real API integration
  - Methods: `fetch()` (gets data), `parse()` (parses response)
- `EspacenetExcelParser`: Parser for Espacenet Excel files
  - Reads Excel files using pandas
  - Methods: `parse()` (single sheet), `parse_multiple_sheets()` (all sheets)
  - Handles file errors gracefully

## Usage

Parse Excel file:
```python
from apps.ingestion.connectors import EspacenetExcelParser
parser = EspacenetExcelParser()
raw_data = parser.parse("path/to/file.xlsx", sheet_name="Countries (family)")
```

Fetch from Lens (mock):
```python
from apps.ingestion.connectors import LensConnector
connector = LensConnector()
response = connector.fetch({"query": "patents"})
raw_data = connector.parse(response)
```

