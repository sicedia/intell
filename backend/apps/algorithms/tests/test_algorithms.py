"""
Tests for all chart generation algorithms.
Tests each algorithm with real Excel files from context/excels.
"""
import pytest
from pathlib import Path
from django.conf import settings

from apps.datasets.models import Dataset
from apps.datasets.normalizers import normalize_from_excel
from apps.algorithms.registry import AlgorithmRegistry


@pytest.fixture
def excel_test_files():
    """Get paths to test Excel files."""
    excel_dir = Path(__file__).parent.parent.parent.parent / 'context' / 'excels'
    files = []
    for excel_file in excel_dir.glob('*.xlsx'):
        if excel_file.exists():
            files.append(excel_file)
    if not files:
        pytest.skip("No Excel test files found in context/excels")
    return files


@pytest.fixture
def excel_test_file():
    """Get first available Excel test file."""
    excel_dir = Path(__file__).parent.parent.parent.parent / 'context' / 'excels'
    excel_file = excel_dir / 'Filters_20250522_1212.xlsx'
    if not excel_file.exists():
        excel_file = excel_dir / 'Filters_20250331_1141.xlsx'
    if not excel_file.exists():
        pytest.skip("No Excel test file found")
    return excel_file


@pytest.mark.django_db
class TestTopPatentCountries:
    """Test top_patent_countries algorithm."""
    
    def test_top_patent_countries_basic(self, excel_test_file):
        """Test basic functionality."""
        # Create dataset from Countries sheet
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Countries (family)")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("top_patent_countries", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {"top_n": 10})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_countries'
    
    def test_top_patent_countries_different_top_n(self, excel_test_file):
        """Test with different top_n values."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Countries (family)")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("top_patent_countries", "1.0")
        
        for top_n in [5, 10, 15, 20]:
            result = algorithm.run(dataset, {"top_n": top_n})
            assert result is not None
            assert len(result.chart_data['series']) <= top_n


@pytest.mark.django_db
class TestTopPatentInventors:
    """Test top_patent_inventors algorithm."""
    
    def test_top_patent_inventors_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Inventors")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("top_patent_inventors", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {"top_n": 10})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_inventors'
    
    def test_top_patent_inventors_validation(self, excel_test_file):
        """Test parameter validation."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Inventors")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("top_patent_inventors", "1.0")
        
        # Test invalid top_n
        with pytest.raises(ValueError):
            algorithm.run(dataset, {"top_n": -1})
        
        with pytest.raises(ValueError):
            algorithm.run(dataset, {"top_n": 0})


@pytest.mark.django_db
class TestTopPatentApplicants:
    """Test top_patent_applicants algorithm."""
    
    def test_top_patent_applicants_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Applicants")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("top_patent_applicants", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {"top_n": 15})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'horizontal_bar'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'top_patent_applicants'


@pytest.mark.django_db
class TestPatentEvolution:
    """Test patent_evolution algorithm."""
    
    def test_patent_evolution_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("patent_evolution", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
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
    
    def test_patent_cumulative_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("patent_cumulative", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
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
    
    def test_patent_trends_cumulative_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("patent_trends_cumulative", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
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
    
    def test_patent_forecast_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("patent_forecast", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'forecast_line'
        assert 'historical_series' in result.chart_data
        assert len(result.chart_data['historical_series']) > 0
        assert 'forecast_years' in result.chart_data
        assert 'warnings' in result.chart_data
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'patent_forecast'
    
    def test_patent_forecast_has_forecasts(self, excel_test_file):
        """Test that forecast data is present (if dependencies available)."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="Earliest publication date (fam")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("patent_forecast", "1.0")
        
        result = algorithm.run(dataset, {})
        
        # Forecasts may or may not be present depending on dependencies
        # But warnings should indicate if they're missing
        if result.chart_data['warnings']:
            # If there are warnings about missing dependencies, that's OK
            assert any('not available' in w.lower() for w in result.chart_data['warnings'])


@pytest.mark.django_db
class TestCPCTreemap:
    """Test cpc_treemap algorithm."""
    
    def test_cpc_treemap_basic(self, excel_test_file):
        """Test basic functionality."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="CPC subgroups")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("cpc_treemap", "1.0")
        
        assert algorithm is not None
        
        result = algorithm.run(dataset, {"num_groups": 15})
        
        assert result is not None
        assert result.png_bytes is not None
        assert len(result.png_bytes) > 0
        assert result.svg_text is not None
        assert result.svg_text.startswith('<svg')
        assert result.chart_data is not None
        assert result.chart_data['type'] == 'treemap'
        assert 'series' in result.chart_data
        assert len(result.chart_data['series']) > 0
        assert result.meta is not None
        assert result.meta['algorithm_key'] == 'cpc_treemap'
    
    def test_cpc_treemap_validation(self, excel_test_file):
        """Test parameter validation."""
        dataset = normalize_from_excel(str(excel_test_file), sheet_name="CPC subgroups")
        
        registry = AlgorithmRegistry()
        algorithm = registry.get("cpc_treemap", "1.0")
        
        # Test invalid num_groups
        with pytest.raises(ValueError):
            algorithm.run(dataset, {"num_groups": -1})
        
        with pytest.raises(ValueError):
            algorithm.run(dataset, {"num_groups": 0})


@pytest.mark.django_db
class TestAllAlgorithmsWithMultipleFiles:
    """Test all algorithms with multiple Excel files."""
    
    def test_all_algorithms_with_all_excel_files(self, excel_test_files):
        """Test that all algorithms work with all available Excel files."""
        registry = AlgorithmRegistry()
        
        # Test configurations: (algorithm_key, sheet_name, params)
        test_configs = [
            ("top_patent_countries", "Countries (family)", {"top_n": 10}),
            ("top_patent_inventors", "Inventors", {"top_n": 10}),
            ("top_patent_applicants", "Applicants", {"top_n": 10}),
            ("patent_evolution", "Earliest publication date (fam", {}),
            ("patent_cumulative", "Earliest publication date (fam", {}),
            ("patent_trends_cumulative", "Earliest publication date (fam", {}),
            ("patent_forecast", "Earliest publication date (fam", {}),
            ("cpc_treemap", "CPC subgroups", {"num_groups": 10}),
        ]
        
        for excel_file in excel_test_files:
            for algorithm_key, sheet_name, params in test_configs:
                try:
                    # Create dataset
                    dataset = normalize_from_excel(str(excel_file), sheet_name=sheet_name)
                    
                    # Get algorithm
                    algorithm = registry.get(algorithm_key, "1.0")
                    
                    if algorithm is None:
                        pytest.skip(f"Algorithm {algorithm_key} not registered")
                    
                    # Run algorithm
                    result = algorithm.run(dataset, params)
                    
                    # Basic assertions
                    assert result is not None, f"Algorithm {algorithm_key} returned None for {excel_file.name}"
                    assert result.png_bytes is not None, f"PNG bytes missing for {algorithm_key}"
                    assert len(result.png_bytes) > 0, f"PNG bytes empty for {algorithm_key}"
                    assert result.svg_text is not None, f"SVG text missing for {algorithm_key}"
                    assert result.chart_data is not None, f"Chart data missing for {algorithm_key}"
                    
                except Exception as e:
                    # Log but don't fail - some sheets might not exist in all files
                    pytest.fail(f"Algorithm {algorithm_key} failed with {excel_file.name}: {str(e)}")

