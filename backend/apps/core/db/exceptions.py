"""
Database-specific exceptions for the Intelli project.

These exceptions provide granular error handling for database operations,
following the Django convention of specific exception hierarchies.
"""

from apps.core.exceptions import IntelliException


class DatabaseError(IntelliException):
    """Base exception for all database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """
    Raised when a database connection cannot be established.
    
    This exception is raised after connection attempts fail,
    but before retry logic is exhausted.
    
    Attributes:
        original_error: The underlying database error that caused the failure.
        attempt: The attempt number when this error was raised.
    """
    
    def __init__(self, message: str, original_error: Exception = None, attempt: int = None):
        super().__init__(message)
        self.original_error = original_error
        self.attempt = attempt
    
    def __str__(self):
        base_msg = super().__str__()
        if self.attempt:
            base_msg = f"[Attempt {self.attempt}] {base_msg}"
        if self.original_error:
            base_msg = f"{base_msg} (caused by: {type(self.original_error).__name__}: {self.original_error})"
        return base_msg


class DatabaseRetryExhaustedError(DatabaseError):
    """
    Raised when all retry attempts have been exhausted.
    
    This exception indicates that the database connection could not be
    established after the configured number of retry attempts.
    
    Attributes:
        max_attempts: The maximum number of attempts that were made.
        total_time: The total time spent attempting to connect (in seconds).
        last_error: The last error that occurred before giving up.
    """
    
    def __init__(
        self, 
        message: str, 
        max_attempts: int = None, 
        total_time: float = None,
        last_error: Exception = None
    ):
        super().__init__(message)
        self.max_attempts = max_attempts
        self.total_time = total_time
        self.last_error = last_error
    
    def __str__(self):
        base_msg = super().__str__()
        details = []
        if self.max_attempts:
            details.append(f"attempts={self.max_attempts}")
        if self.total_time:
            details.append(f"total_time={self.total_time:.2f}s")
        if self.last_error:
            details.append(f"last_error={type(self.last_error).__name__}")
        if details:
            base_msg = f"{base_msg} ({', '.join(details)})"
        return base_msg


class DatabaseQueryError(DatabaseError):
    """
    Raised when a database query fails due to connection issues.
    
    This is different from Django's IntegrityError or DataError,
    which are related to data issues rather than connection issues.
    """
    
    def __init__(self, message: str, query: str = None, original_error: Exception = None):
        super().__init__(message)
        self.query = query
        self.original_error = original_error


class DatabaseTimeoutError(DatabaseError):
    """
    Raised when a database operation times out.
    
    This can happen during connection establishment or query execution.
    """
    
    def __init__(self, message: str, timeout_seconds: float = None, operation: str = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds
        self.operation = operation
    
    def __str__(self):
        base_msg = super().__str__()
        if self.operation and self.timeout_seconds:
            base_msg = f"{base_msg} (operation={self.operation}, timeout={self.timeout_seconds}s)"
        return base_msg
