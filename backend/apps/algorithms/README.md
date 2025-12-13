# Algorithms App

This app manages chart generation algorithms for patent data visualization.

## Architecture

All algorithms must:
- Extend `BaseAlgorithm` abstract class
- Consume `datasets.Dataset` (never raw data)
- Return `ChartResult` with `png_bytes`, `svg_text`, `chart_data`, and `meta`
- Be registered in `AlgorithmRegistry`

## Available Algorithms

### 1. Top Patent Countries (`top_patent_countries`)
- **Description**: Horizontal bar chart showing top n jurisdictions by patent publications
- **Data Source**: Excel sheet "Countries (family)"
- **Parameters**:
  - `top_n` (int, default: 15): Number of countries to display
- **Output**: PNG, SVG, chart_data with series, percentages, and metadata

### 2. Top Patent Inventors (`top_patent_inventors`)
- **Description**: Horizontal bar chart showing top n inventors by patent publications
- **Data Source**: Excel sheet "Inventors"
- **Parameters**:
  - `top_n` (int, default: 10): Number of inventors to display
- **Output**: PNG, SVG, chart_data with series, percentages, and metadata

### 3. Top Patent Applicants (`top_patent_applicants`)
- **Description**: Horizontal bar chart showing top n patent applicants by publications
- **Data Source**: Excel sheet "Applicants"
- **Parameters**:
  - `top_n` (int, default: 15): Number of applicants to display
- **Output**: PNG, SVG, chart_data with series, percentages, and metadata

### 4. Patent Evolution (`patent_evolution`)
- **Description**: Line chart showing annual evolution of patent publications
- **Data Source**: Excel sheet "Earliest publication date (fam"
- **Parameters**: None (uses default historical_years=20, cutoff_year=current_year-2)
- **Output**: PNG, SVG, chart_data with time series data

### 5. Patent Cumulative (`patent_cumulative`)
- **Description**: Line chart showing cumulative evolution of patent publications
- **Data Source**: Excel sheet "Earliest publication date (fam"
- **Parameters**: None (uses default historical_years=20, cutoff_year=current_year-2)
- **Output**: PNG, SVG, chart_data with cumulative series data

### 6. Patent Trends Cumulative (`patent_trends_cumulative`)
- **Description**: Dual-axis line chart showing both annual and cumulative evolution
- **Data Source**: Excel sheet "Earliest publication date (fam"
- **Parameters**: None (uses default historical_years=20, cutoff_year=current_year-2)
- **Output**: PNG, SVG, chart_data with both series

### 7. Patent Forecast (`patent_forecast`)
- **Description**: Line chart with historical data, CAGR projection, and ETS/ARIMA forecasts
- **Data Source**: Excel sheet "Earliest publication date (fam"
- **Parameters**: None (uses default historical_years=20, cutoff_year=current_year-2)
- **Dependencies**: `statsmodels`, `pmdarima` (optional, with fallback)
- **Output**: PNG, SVG, chart_data with historical and forecast series

### 8. CPC Treemap (`cpc_treemap`)
- **Description**: Treemap visualization of top CPC subgroups by patent publications
- **Data Source**: Excel sheet "CPC subgroups"
- **Parameters**:
  - `num_groups` (int, default: 15): Number of CPC subgroups to display
- **Dependencies**: `squarify` (required)
- **Output**: PNG, SVG, chart_data with treemap series

## File Naming

Generated artifacts are saved with the following naming convention:
- PNG: `job_{job_id}_task_{task_id}.png`
- SVG: `job_{job_id}_task_{task_id}.svg`

These files are stored in `MEDIA_ROOT/artifacts/png/` and `MEDIA_ROOT/artifacts/svg/` respectively.

## Chart Data Structure

All algorithms return `chart_data` in a consistent structure:

```python
{
    'type': str,  # Chart type (e.g., 'horizontal_bar', 'line', 'treemap', 'forecast_line')
    'x_axis': str,  # X-axis label
    'y_axis': str,  # Y-axis label (or y_axis_1, y_axis_2 for dual-axis)
    'series': list,  # Data series (format varies by chart type)
    'total_publications': int,  # Total (if applicable)
    'years_range': dict,  # For time series charts
    'warnings': list  # Any warnings during processing
}
```

## Usage Example

```python
from apps.algorithms.registry import AlgorithmRegistry
from apps.datasets.models import Dataset

# Get algorithm
registry = AlgorithmRegistry()
algorithm = registry.get("top_patent_countries", "1.0")

# Execute
dataset = Dataset.objects.get(id=1)
result = algorithm.run(dataset, params={"top_n": 10})

# Access results
png_bytes = result.png_bytes
svg_text = result.svg_text
chart_data = result.chart_data
meta = result.meta
```

## Adding New Algorithms

1. Create a new file in `apps/algorithms/demo/`
2. Extend `BaseAlgorithm` and implement `run()` method
3. Register in `apps/algorithms/apps.py` in the `ready()` method
4. Ensure algorithm consumes `Dataset` and returns `ChartResult`

## Dependencies

- **Required**: `pandas`, `matplotlib`, `numpy`
- **Optional**: `statsmodels`, `pmdarima` (for forecast), `squarify` (for treemap)
