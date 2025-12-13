# Algorithm Tests

This directory contains comprehensive tests for all chart generation algorithms.

## Test Files

- **`test_registry.py`**: Tests for AlgorithmRegistry functionality
- **`test_algorithms.py`**: Basic tests for algorithms (legacy)
- **`test_all_algorithms.py`**: Comprehensive tests for all algorithms using real Excel data

## Running Tests

### Run all algorithm tests:
```bash
pytest apps/algorithms/tests/
```

### Run specific test file:
```bash
pytest apps/algorithms/tests/test_all_algorithms.py
```

### Run specific test class:
```bash
pytest apps/algorithms/tests/test_all_algorithms.py::TestTopPatentCountries
```

### Run with verbose output:
```bash
pytest apps/algorithms/tests/test_all_algorithms.py -v
```

## Test Coverage

The `test_all_algorithms.py` file tests all 8 algorithms:

1. **Top Patent Countries** (`top_patent_countries`)
2. **Top Patent Inventors** (`top_patent_inventors`)
3. **Top Patent Applicants** (`top_patent_applicants`)
4. **Patent Evolution** (`patent_evolution`)
5. **Patent Cumulative** (`patent_cumulative`)
6. **Patent Trends Cumulative** (`patent_trends_cumulative`)
7. **Patent Forecast** (`patent_forecast`)
8. **CPC Treemap** (`cpc_treemap`)

## Test Data

Tests use real Excel files from `backend/context/excels/`:
- `Filters_20250522_1212.xlsx`
- `Filters_20250331_1141.xlsx`

Each algorithm is tested with the appropriate Excel sheet:
- **Countries sheet**: `top_patent_countries`
- **Inventors sheet**: `top_patent_inventors`
- **Applicants sheet**: `top_patent_applicants`
- **Earliest publication date sheet**: `patent_evolution`, `patent_cumulative`, `patent_trends_cumulative`, `patent_forecast`
- **CPC subgroups sheet**: `cpc_treemap`

## What Tests Verify

For each algorithm, tests verify:

1. **Registration**: Algorithm is registered in the registry
2. **Execution**: Algorithm runs successfully with default parameters
3. **Output Quality**: 
   - PNG bytes are generated and non-empty
   - SVG text is generated and valid
   - Chart data structure is correct
   - Metadata is present and correct
4. **Parameter Handling**: Algorithm accepts and validates custom parameters
5. **Integration**: All algorithms work together in integration scenarios

## Dependencies

Tests require:
- `pytest` and `pytest-django`
- All algorithm dependencies (pandas, matplotlib, numpy, etc.)
- Optional dependencies for specific algorithms:
  - `squarify` for treemap
  - `statsmodels` and `pmdarima` for forecast (with graceful fallback)

## Notes

- Tests use `@pytest.mark.django_db` to ensure database access
- Fixtures automatically find Excel files in multiple possible locations
- Tests skip gracefully if Excel files are not found
- Forecast algorithm tests handle missing dependencies gracefully

