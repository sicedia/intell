"""
Comprehensive tests for all chart generation algorithms.
Tests use real Excel files from backend/context/excels/.
"""
import pytest
from pathlib import Path
from django.conf import settings
import json

from apps.datasets.models import Dataset
from apps.datasets.normalizers import normalize_from_excel
from apps.algorithms.registry import AlgorithmRegistry


@pytest.fixture
def excel_test_files():
    """Get all available Excel test files."""
    # Try multiple possible paths
    possible_paths = [
        Path(__file__).parent.parent.parent / 'context' / 'excels',
        Path(__file__).parent.parent.parent.parent / 'context' / 'excels',
        Path(__file__).parent.parent.parent / 'context',
    ]
    
    files = []
    for base_path in possible_paths:
        if base_path.exists():
            for filename in ['Filters_20250522_1212.xlsx', 'Filters_20250331_1141.xlsx']:
                file_path = base_path / filename
                if file_path.exists() and file_path not in files:
                    files.append(file_path)
    
    if not files:
        pytest.skip("No Excel test files found")
    
    return files


@pytest.fixture
def excel_test_file():
    """Get first available Excel test file."""
    # Try multiple possible paths
    possible_paths = [
        Path(__file__).parent.parent.parent / 'context' / 'excels',
        Path(__file__).parent.parent.parent.parent / 'context' / 'excels',
        Path(__file__).parent.parent.parent / 'context',
    ]
    
    for base_path in possible_paths:
        if base_path.exists():
            for filename in ['Filters_20250522_1212.xlsx', 'Filters_20250331_1141.xlsx']:
                file_path = base_path / filename
                if file_path.exists():
                    return file_path
    
    pytest.skip("No Excel test file found")


@pytest.fixture
def dataset_countries(db, excel_test_file):
    """Create Dataset from Countries sheet."""
    return normalize_from_excel(str(excel_test_file), sheet_name="Countries (family)")


@pytest.fixture
def dataset_inventors(db, excel_test_file):
    """Create Dataset from Inventors sheet."""
    return normalize_from_excel(str(excel_test_file), sheet_name="Inventors")


@pytest.fixture
def dataset_applicants(db, excel_test_file):
    """Create Dataset from Applicants sheet."""
    return normalize_from_excel(str(excel_test_file), sheet_name="Applicants")


@pytest.fixture
def dataset_publication_date(db, excel_test_file):
    """Create Dataset from Earliest publication date sheet."""
    return normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")


@pytest.fixture
def dataset_cpc_subgroups(db, excel_test_file):
    """Create Dataset from CPC subgroups sheet."""
    return normalize_from_excel(str(excel_test_file), sheet_name="CPC subgroups")


@pytest.fixture
def algorithm_registry():
    """Get algorithm registry instance."""
    return AlgorithmRegistry()


@pytest.mark.django_db
class TestTopPatentCountries:
    """Test top_patent_countries algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("top_patent_countries", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_countries):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("top_patent_countries", "1.0")
        result = algo.run(dataset_countries, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_countries'
    
    def test_run_with_custom_top_n(self, algorithm_registry, dataset_countries):
        """Test algorithm execution with custom top_n."""
        algo = algorithm_registry.get("top_patent_countries", "1.0")
        result = algo.run(dataset_countries, {"top_n": 10})
        
        assert result is not None
        assert result.chart_data is not None
        assert len(result.chart_data['series']) <= 12  # top_n + Others + possibly Ecuador


@pytest.mark.django_db
class TestTopPatentInventors:
    """Test top_patent_inventors algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("top_patent_inventors", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_inventors):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("top_patent_inventors", "1.0")
        result = algo.run(dataset_inventors, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_inventors'
    
    def test_run_with_custom_top_n(self, algorithm_registry, dataset_inventors):
        """Test algorithm execution with custom top_n."""
        algo = algorithm_registry.get("top_patent_inventors", "1.0")
        result = algo.run(dataset_inventors, {"top_n": 5})
        
        assert result is not None
        assert result.chart_data is not None
        assert len(result.chart_data['series']) <= 5


@pytest.mark.django_db
class TestTopPatentApplicants:
    """Test top_patent_applicants algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("top_patent_applicants", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_applicants):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("top_patent_applicants", "1.0")
        result = algo.run(dataset_applicants, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_applicants'
    
    def test_run_with_custom_top_n(self, algorithm_registry, dataset_applicants):
        """Test algorithm execution with custom top_n."""
        algo = algorithm_registry.get("top_patent_applicants", "1.0")
        result = algo.run(dataset_applicants, {"top_n": 8})
        
        assert result is not None
        assert result.chart_data is not None
        assert len(result.chart_data['series']) <= 8


@pytest.mark.django_db
class TestPatentEvolution:
    """Test patent_evolution algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("patent_evolution", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_publication_date):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("patent_evolution", "1.0")
        result = algo.run(dataset_publication_date, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'line'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert 'years_range' in result.chart_data
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'patent_evolution'


@pytest.mark.django_db
class TestPatentCumulative:
    """Test patent_cumulative algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("patent_cumulative", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_publication_date):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("patent_cumulative", "1.0")
        result = algo.run(dataset_publication_date, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'line'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert 'total_cumulative' in result.chart_data
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'patent_cumulative'


@pytest.mark.django_db
class TestPatentTrendsCumulative:
    """Test patent_trends_cumulative algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("patent_trends_cumulative", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_publication_date):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("patent_trends_cumulative", "1.0")
        result = algo.run(dataset_publication_date, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'dual_axis_line'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert 'y_axis_1' in result.chart_data
        assert 'y_axis_2' in result.chart_data
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'patent_trends_cumulative'


@pytest.mark.django_db
class TestPatentForecast:
    """Test patent_forecast algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("patent_forecast", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_publication_date):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("patent_forecast", "1.0")
        result = algo.run(dataset_publication_date, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'forecast_line'
        assert 'historical_series' in result.chart_data
        assert len(result.chart_data['historical_series']) > 0
        assert 'forecast_years' in result.chart_data
        assert 'warnings' in result.chart_data
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'patent_forecast'
        
        # Check if forecasts are available (may be None if dependencies missing)
        assert 'forecast_ets' in result.chart_data
        assert 'forecast_arima' in result.chart_data


@pytest.mark.django_db
class TestCPCTreemap:
    """Test cpc_treemap algorithm."""
    
    def test_algorithm_registered(self, algorithm_registry):
        """Test that algorithm is registered."""
        algo = algorithm_registry.get("cpc_treemap", "1.0")
        assert algo is not None
    
    def test_run_with_default_params(self, algorithm_registry, dataset_cpc_subgroups):
        """Test algorithm execution with default parameters."""
        algo = algorithm_registry.get("cpc_treemap", "1.0")
        result = algo.run(dataset_cpc_subgroups, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert len(result.svg_text) > 0
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'treemap'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'cpc_treemap'
    
    def test_run_with_custom_num_groups(self, algorithm_registry, dataset_cpc_subgroups):
        """Test algorithm execution with custom num_groups."""
        algo = algorithm_registry.get("cpc_treemap", "1.0")
        result = algo.run(dataset_cpc_subgroups, {"num_groups": 10})
        
        assert result is not None
        assert result.chart_data is not None
        assert len(result.chart_data['series']) <= 10


@pytest.mark.django_db
class TestAllAlgorithmsIntegration:
    """Integration tests for all algorithms with real Excel data."""
    
    def test_all_algorithms_produce_valid_outputs(self, algorithm_registry, excel_test_file):
        """Test that all algorithms can process real Excel data and produce valid outputs."""
        registry = algorithm_registry
        
        # Test each algorithm with appropriate dataset
        algorithms_to_test = [
            ("top_patent_countries", "Countries (family)"),
            ("top_patent_inventors", "Inventors"),
            ("top_patent_applicants", "Applicants"),
            ("patent_evolution", "Earliest publication date (fam"),
            ("patent_cumulative", "Earliest publication date (fam"),
            ("patent_trends_cumulative", "Earliest publication date (fam"),
            ("patent_forecast", "Earliest publication date (fam"),
            ("cpc_treemap", "CPC subgroups"),
        ]
        
        for algo_key, sheet_name in algorithms_to_test:
            try:
                # Create dataset
                dataset = normalize_from_excel(str(excel_test_file), sheet_name=sheet_name)
                
                # Get algorithm
                algo = registry.get(algo_key, "1.0")
                assert algo is not None, f"Algorithm {algo_key} not found"
                
                # Run algorithm with default params
                params = {}
                if algo_key in ["top_patent_countries", "top_patent_inventors", "top_patent_applicants"]:
                    params = {"top_n": 10}
                elif algo_key == "cpc_treemap":
                    params = {"num_groups": 10}
                
                result = algo.run(dataset, params)
                
                # Verify results
                assert result is not None, f"Algorithm {algo_key} returned None"
                assert result.png_bytes is not None, f"Algorithm {algo_key} produced no PNG"
                assert len(result.png_bytes) > 100, f"Algorithm {algo_key} produced invalid PNG (too small)"
                assert result.svg_text is not None, f"Algorithm {algo_key} produced no SVG"
                assert len(result.svg_text) > 100, f"Algorithm {algo_key} produced invalid SVG (too small)"
                assert result.chart_data is not None, f"Algorithm {algo_key} produced no chart_data"
                assert 'type' in result.chart_data, f"Algorithm {algo_key} chart_data missing type"
                assert result.meta is not None, f"Algorithm {algo_key} produced no meta"
                assert result.meta['algorithm_key'] == algo_key, f"Algorithm {algo_key} meta has wrong key"
                
            except Exception as e:
                pytest.fail(f"Algorithm {algo_key} failed with error: {str(e)}")
    
    def test_chart_data_structure_consistency(self, algorithm_registry, excel_test_file):
        """Test that all algorithms return consistent chart_data structure."""
        registry = algorithm_registry
        
        # Test a few algorithms
        test_cases = [
            ("top_patent_countries", "Countries (family)", {"top_n": 5}),
            ("patent_evolution", "Earliest publication date (fam", {}),
            ("cpc_treemap", "CPC subgroups", {"num_groups": 5}),
        ]
        
        for algo_key, sheet_name, params in test_cases:
            dataset = normalize_from_excel(str(excel_test_file), sheet_name=sheet_name)
            algo = registry.get(algo_key, "1.0")
            result = algo.run(dataset, params)
            
            chart_data = result.chart_data
            
            # All should have type
            assert 'type' in chart_data
            
            # All should have series or equivalent
            assert 'series' in chart_data or 'historical_series' in chart_data
            
            # All should have warnings list
            assert 'warnings' in chart_data
            assert isinstance(chart_data['warnings'], list)

