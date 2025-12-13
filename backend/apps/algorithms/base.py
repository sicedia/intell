"""
Base algorithm contract.
All algorithms must implement BaseAlgorithm and consume datasets.Dataset.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any
from apps.datasets.models import Dataset


@dataclass
class ChartResult:
    """
    Result from algorithm execution.
    Contains chart data in multiple formats and metadata for AI processing.
    """
    png_bytes: Optional[bytes] = None
    svg_text: Optional[str] = None
    chart_data: Dict[str, Any] = None  # Structured data for AI
    meta: Dict[str, Any] = None  # Metadata (versions, execution time, etc.)
    
    def __post_init__(self):
        """Initialize default values."""
        if self.chart_data is None:
            self.chart_data = {}
        if self.meta is None:
            self.meta = {}


class BaseAlgorithm(ABC):
    """
    Abstract base class for all chart generation algorithms.
    
    All algorithms must:
    - Receive datasets.Dataset (never raw data)
    - Return ChartResult with png_bytes, svg_text, chart_data, and meta
    """
    
    def __init__(self, algorithm_key: str, algorithm_version: str):
        """
        Initialize algorithm.
        
        Args:
            algorithm_key: Unique identifier for the algorithm
            algorithm_version: Version string
        """
        self.algorithm_key = algorithm_key
        self.algorithm_version = algorithm_version
    
    @abstractmethod
    def run(self, dataset: Dataset, params: Dict[str, Any]) -> ChartResult:
        """
        Execute algorithm on dataset.
        
        Args:
            dataset: Dataset instance (canonical format)
            params: Algorithm-specific parameters
            
        Returns:
            ChartResult with generated chart and metadata
        """
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate algorithm parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        return True

