"""
Algorithm registry for managing and retrieving algorithms.
"""
from typing import Dict, Optional
from .base import BaseAlgorithm


class AlgorithmRegistry:
    """
    Singleton registry for algorithms.
    Maps (algorithm_key, algorithm_version) to algorithm instances.
    """
    _instance = None
    _algorithms: Dict[tuple, BaseAlgorithm] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(AlgorithmRegistry, cls).__new__(cls)
        return cls._instance
    
    def register(self, algorithm_key: str, algorithm_version: str, algorithm: BaseAlgorithm):
        """
        Register an algorithm.
        
        Args:
            algorithm_key: Unique identifier for the algorithm
            algorithm_version: Version string
            algorithm: Algorithm instance
        """
        key = (algorithm_key, algorithm_version)
        self._algorithms[key] = algorithm
    
    def get(self, algorithm_key: str, algorithm_version: str) -> Optional[BaseAlgorithm]:
        """
        Get algorithm by key and version.
        
        Args:
            algorithm_key: Unique identifier for the algorithm
            algorithm_version: Version string
            
        Returns:
            Algorithm instance or None if not found
        """
        key = (algorithm_key, algorithm_version)
        return self._algorithms.get(key)
    
    def list_algorithms(self) -> Dict[tuple, str]:
        """
        List all registered algorithms.
        
        Returns:
            Dictionary mapping (key, version) to algorithm class name
        """
        return {
            key: algorithm.__class__.__name__
            for key, algorithm in self._algorithms.items()
        }

