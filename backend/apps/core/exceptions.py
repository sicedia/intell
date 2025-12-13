"""
Custom exceptions for the Intelli project.
"""


class IntelliException(Exception):
    """Base exception for all Intelli-specific exceptions."""
    pass


class ValidationError(IntelliException):
    """Raised when data validation fails."""
    pass


class ExternalAPIError(IntelliException):
    """Raised when external API calls fail."""
    pass


class AlgorithmError(IntelliException):
    """Raised when algorithm execution fails."""
    pass


class RenderError(IntelliException):
    """Raised when chart rendering fails."""
    pass


class StorageError(IntelliException):
    """Raised when storage operations fail."""
    pass


class AIProviderError(IntelliException):
    """Raised when AI provider calls fail."""
    pass

