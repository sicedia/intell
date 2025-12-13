"""
Unit tests for AlgorithmRegistry.
"""
import pytest
from apps.algorithms.registry import AlgorithmRegistry
from apps.algorithms.base import BaseAlgorithm, ChartResult
from apps.algorithms.demo.top_patent_countries import TopPatentCountriesAlgorithm


class MockAlgorithm(BaseAlgorithm):
    """Mock algorithm for testing."""
    
    def __init__(self):
        """Initialize mock algorithm."""
        super().__init__("mock_algorithm", "1.0")
    
    def run(self, dataset, params):
        """Mock run method."""
        return ChartResult(
            png_bytes=b'fake_png',
            svg_text='<svg></svg>',
            chart_data={'type': 'bar', 'series': []},
            meta={'version': '1.0'}
        )


@pytest.mark.django_db
class TestAlgorithmRegistry:
    """Test AlgorithmRegistry functionality."""
    
    def test_register_algorithm(self):
        """Test registering an algorithm."""
        registry = AlgorithmRegistry()
        algorithm = TopPatentCountriesAlgorithm()
        
        registry.register("test_algorithm", "1.0", algorithm)
        
        # Verify registration
        retrieved = registry.get("test_algorithm", "1.0")
        assert retrieved is not None
        assert retrieved == algorithm
    
    def test_get_algorithm(self):
        """Test retrieving a registered algorithm."""
        registry = AlgorithmRegistry()
        algorithm = TopPatentCountriesAlgorithm()
        
        registry.register("test_algorithm", "1.0", algorithm)
        
        # Get with exact version
        retrieved = registry.get("test_algorithm", "1.0")
        assert retrieved == algorithm
        
        # Get with different version
        algorithm_v2 = TopPatentCountriesAlgorithm()
        registry.register("test_algorithm", "2.0", algorithm_v2)
        retrieved_v2 = registry.get("test_algorithm", "2.0")
        assert retrieved_v2 == algorithm_v2
    
    def test_get_nonexistent_algorithm(self):
        """Test retrieving a non-existent algorithm."""
        registry = AlgorithmRegistry()
        
        retrieved = registry.get("nonexistent", "1.0")
        assert retrieved is None
    
    def test_register_multiple_versions(self):
        """Test registering multiple versions of the same algorithm."""
        registry = AlgorithmRegistry()
        algo_v1 = MockAlgorithm()
        algo_v2 = MockAlgorithm()
        
        registry.register("test_algorithm", "1.0", algo_v1)
        registry.register("test_algorithm", "2.0", algo_v2)
        
        # Get specific versions
        assert registry.get("test_algorithm", "1.0") == algo_v1
        assert registry.get("test_algorithm", "2.0") == algo_v2
    
    def test_list_algorithms(self):
        """Test listing all registered algorithms."""
        registry = AlgorithmRegistry()
        
        # Register multiple algorithms
        registry.register("algo1", "1.0", MockAlgorithm())
        registry.register("algo2", "1.0", MockAlgorithm())
        registry.register("algo1", "2.0", MockAlgorithm())
        
        # List should return dict of (key, version) -> description
        algorithms = registry.list_algorithms()
        assert isinstance(algorithms, dict)
        assert ("algo1", "1.0") in algorithms
        assert ("algo2", "1.0") in algorithms
        assert ("algo1", "2.0") in algorithms
    
    def test_register_overwrite(self):
        """Test that registering the same key+version overwrites."""
        registry = AlgorithmRegistry()
        algo1 = MockAlgorithm()
        algo2 = MockAlgorithm()
        
        registry.register("test_algorithm", "1.0", algo1)
        registry.register("test_algorithm", "1.0", algo2)
        
        # Should return the last registered
        retrieved = registry.get("test_algorithm", "1.0")
        assert retrieved == algo2

