"""
Script to test patent algorithms directly with Excel files.
This simulates what happens in the application when processing datasets.
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

import pandas as pd
from pathlib import Path
import json
import tempfile
from unittest.mock import MagicMock

# Import all algorithms
from apps.algorithms.demo.patent_evolution import PatentEvolutionAlgorithm
from apps.algorithms.demo.patent_cumulative import PatentCumulativeAlgorithm
from apps.algorithms.demo.patent_trends_cumulative import PatentTrendsCumulativeAlgorithm
from apps.algorithms.demo.patent_forecast import PatentForecastAlgorithm
from apps.algorithms.demo.top_patent_applicants import TopPatentApplicantsAlgorithm
from apps.algorithms.demo.top_patent_inventors import TopPatentInventorsAlgorithm
from apps.algorithms.demo.top_patent_countries import TopPatentCountriesAlgorithm
from apps.algorithms.demo.cpc_treemap import CPCTreemapAlgorithm


def create_mock_dataset(json_path: str, normalized_format: str = 'json', dataset_id: int = 1):
    """Create a mock Dataset object for testing."""
    mock_dataset = MagicMock()
    mock_dataset.storage_path = json_path
    mock_dataset.normalized_format = normalized_format
    mock_dataset.id = dataset_id
    return mock_dataset


def excel_sheet_to_json(excel_path: str, sheet_name: str, output_path: str) -> str:
    """Convert an Excel sheet to JSON file."""
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    # Convert to list of dicts
    data = df.to_dict(orient='records')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return output_path


def test_algorithm(algorithm_class, algorithm_name: str, json_path: str, params: dict = None):
    """Test a single algorithm with the given JSON data."""
    print(f"\n{'='*60}")
    print(f"Testing: {algorithm_name}")
    print(f"{'='*60}")
    
    if params is None:
        params = {}
    
    try:
        # Create algorithm instance
        algorithm = algorithm_class()
        
        # Create mock dataset
        mock_dataset = create_mock_dataset(json_path)
        
        # Run algorithm
        result = algorithm.run(mock_dataset, params)
        
        print(f"[OK] SUCCESS!")
        print(f"  - PNG size: {len(result.png_bytes)} bytes")
        print(f"  - SVG size: {len(result.svg_text)} chars")
        print(f"  - Chart data keys: {list(result.chart_data.keys())}")
        print(f"  - Meta: {result.meta}")
        
        if result.chart_data.get('warnings'):
            print(f"  - Warnings: {result.chart_data['warnings']}")
        
        # Save outputs for inspection
        output_dir = Path(__file__).parent.parent / 'context' / 'test_outputs'
        output_dir.mkdir(exist_ok=True)
        
        png_path = output_dir / f"{algorithm_name}.png"
        svg_path = output_dir / f"{algorithm_name}.svg"
        
        with open(png_path, 'wb') as f:
            f.write(result.png_bytes)
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(result.svg_text)
        
        print(f"  - Saved PNG: {png_path}")
        print(f"  - Saved SVG: {svg_path}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def find_sheet_by_keyword(xlsx, keyword: str) -> str:
    """Find a sheet name containing the keyword."""
    for name in xlsx.sheet_names:
        if keyword.lower() in name.lower():
            return name
    return None


def main():
    """Main function to test all patent algorithms."""
    excels_folder = Path(__file__).parent.parent / 'context' / 'excels'
    
    # Use the specific Excel file (1141)
    excel_files = list(excels_folder.glob('*1141*.xlsx'))
    if not excel_files:
        # Fallback to any Excel file
        excel_files = list(excels_folder.glob('*.xlsx'))
    if not excel_files:
        print("No Excel files found!")
        return
    
    excel_path = str(excel_files[0])
    print(f"Using Excel file: {excel_path}")
    
    xlsx = pd.ExcelFile(excel_path)
    print(f"Available sheets: {xlsx.sheet_names}")
    
    # Create temp dir for JSON files
    temp_dir = Path(__file__).parent.parent / 'context' / 'test_temp'
    temp_dir.mkdir(exist_ok=True)
    
    # Define algorithm tests with their corresponding sheets
    algorithm_tests = [
        # (AlgorithmClass, name, sheet_keyword, params)
        (PatentEvolutionAlgorithm, "patent_evolution", "earliest publication date", {}),
        (PatentCumulativeAlgorithm, "patent_cumulative", "earliest publication date", {}),
        (PatentTrendsCumulativeAlgorithm, "patent_trends_cumulative", "earliest publication date", {}),
        (PatentForecastAlgorithm, "patent_forecast", "earliest publication date", {}),
        (TopPatentApplicantsAlgorithm, "top_patent_applicants", "applicants", {"top_n": 10}),
        (TopPatentInventorsAlgorithm, "top_patent_inventors", "inventors", {"top_n": 10}),
        (TopPatentCountriesAlgorithm, "top_patent_countries", "countries (family)", {"top_n": 10}),
        (CPCTreemapAlgorithm, "cpc_treemap", "cpc subgroups", {"num_groups": 10}),
    ]
    
    results = {}
    
    for algorithm_class, name, sheet_keyword, params in algorithm_tests:
        # Find the sheet
        sheet_name = find_sheet_by_keyword(xlsx, sheet_keyword)
        
        if not sheet_name:
            print(f"\n[SKIP] {name}: Could not find sheet with keyword '{sheet_keyword}'")
            results[name] = False
            continue
        
        print(f"\n--- Using sheet '{sheet_name}' for {name} ---")
        
        # Convert to JSON
        json_path = str(temp_dir / f'{name}_data.json')
        excel_sheet_to_json(excel_path, sheet_name, json_path)
        
        # Show data preview
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        print(f"Columns: {list(df.columns)}")
        print(f"Rows: {len(df)}")
        print(f"First 3 rows:")
        print(df.head(3).to_string())
        
        # Test the algorithm
        results[name] = test_algorithm(algorithm_class, name, json_path, params)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    for name, success in results.items():
        status = "[OK] PASS" if success else "[FAIL] FAIL"
        print(f"  {name}: {status}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nTotal: {passed}/{total} algorithms passed")


if __name__ == '__main__':
    main()
