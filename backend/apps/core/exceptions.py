"""
Custom exceptions for the Intelli project.

This module provides a hierarchy of exceptions for different error scenarios:
- IntelliException: Base for all project exceptions
- Database errors: Connection, retry, query, and timeout errors
- External service errors: API calls, AI providers
- Processing errors: Validation, algorithms, rendering, storage
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


# Database-related exceptions are defined in apps.core.db.exceptions
# and can be imported from there for more specific error handling:
#
#   from apps.core.db.exceptions import (
#       DatabaseConnectionError,
#       DatabaseRetryExhaustedError,
#       DatabaseQueryError,
#       DatabaseTimeoutError,
#   )
#
# Or use the convenience imports from apps.core.db:
#
#   from apps.core.db import DatabaseConnectionError, DatabaseRetryExhaustedError

