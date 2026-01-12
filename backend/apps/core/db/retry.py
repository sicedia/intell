"""
Database retry utilities with exponential backoff.

This module implements the Retry Pattern with Exponential Backoff,
a standard pattern for handling transient failures in distributed systems.

The implementation follows these best practices:
1. Exponential backoff with jitter to prevent thundering herd
2. Configurable retry limits and timeouts
3. Logging of retry attempts for observability
4. Clean separation of retry logic from business logic

References:
- https://docs.djangoproject.com/en/stable/ref/databases/
- https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
"""

import functools
import logging
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, Type, Union

from django.conf import settings
from django.db import (
    OperationalError,
    InterfaceError,
    connection,
    connections,
)

from .exceptions import (
    DatabaseConnectionError,
    DatabaseRetryExhaustedError,
)

logger = logging.getLogger(__name__)

# Database errors that indicate transient connection issues
# These are the errors we should retry on
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    OperationalError,
    InterfaceError,
)


@dataclass
class DatabaseRetryConfig:
    """
    Configuration for database retry behavior.
    
    This follows the Exponential Backoff with Jitter pattern:
    - Each retry waits longer than the previous one (exponential)
    - Random jitter prevents multiple clients from retrying simultaneously
    - Maximum delay and attempts prevent infinite waiting
    
    Attributes:
        max_attempts: Maximum number of connection attempts (default: 5)
        initial_delay: Initial delay between retries in seconds (default: 0.1)
        max_delay: Maximum delay between retries in seconds (default: 30)
        exponential_base: Base for exponential backoff calculation (default: 2)
        jitter: Whether to add random jitter to delays (default: True)
        jitter_factor: Maximum jitter as a fraction of delay (default: 0.1)
        retryable_exceptions: Tuple of exception types to retry on
    """
    
    max_attempts: int = 5
    initial_delay: float = 0.1
    max_delay: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: RETRYABLE_EXCEPTIONS
    )
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for a given attempt number.
        
        Uses exponential backoff with optional jitter:
        delay = min(max_delay, initial_delay * (exponential_base ** attempt))
        
        Args:
            attempt: The current attempt number (0-indexed)
            
        Returns:
            The delay in seconds before the next retry
        """
        delay = min(
            self.max_delay,
            self.initial_delay * (self.exponential_base ** attempt)
        )
        
        if self.jitter:
            # Add random jitter: ±jitter_factor of the delay
            jitter_range = delay * self.jitter_factor
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)  # Ensure non-negative


def get_retry_config() -> DatabaseRetryConfig:
    """
    Get the database retry configuration from Django settings.
    
    Reads from settings.DATABASE_RETRY_CONFIG if available,
    otherwise returns default configuration.
    
    Returns:
        DatabaseRetryConfig instance with current settings
    """
    config_dict = getattr(settings, 'DATABASE_RETRY_CONFIG', {})
    
    return DatabaseRetryConfig(
        max_attempts=config_dict.get('MAX_ATTEMPTS', 5),
        initial_delay=config_dict.get('INITIAL_DELAY', 0.1),
        max_delay=config_dict.get('MAX_DELAY', 30.0),
        exponential_base=config_dict.get('EXPONENTIAL_BASE', 2.0),
        jitter=config_dict.get('JITTER', True),
        jitter_factor=config_dict.get('JITTER_FACTOR', 0.1),
    )


def execute_with_retry(
    func: Callable,
    config: Optional[DatabaseRetryConfig] = None,
    database: str = 'default',
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
) -> any:
    """
    Execute a function with database retry logic.
    
    This function wraps any callable and adds retry logic for
    transient database connection failures.
    
    Args:
        func: The function to execute
        config: Retry configuration (uses default if not provided)
        database: The database alias to use for connection checks
        on_retry: Optional callback called on each retry with (attempt, error, delay)
        
    Returns:
        The return value of the function
        
    Raises:
        DatabaseRetryExhaustedError: If all retry attempts fail
        
    Example:
        def get_users():
            return User.objects.all()
        
        users = execute_with_retry(get_users)
    """
    if config is None:
        config = get_retry_config()
    
    last_error = None
    start_time = time.time()
    
    for attempt in range(config.max_attempts):
        try:
            # Ensure connection is available before executing
            conn = connections[database]
            conn.ensure_connection()
            
            return func()
            
        except config.retryable_exceptions as e:
            last_error = e
            
            # Log the retry attempt
            logger.warning(
                "Database connection attempt %d/%d failed: %s",
                attempt + 1,
                config.max_attempts,
                str(e),
            )
            
            # Check if we have more attempts
            if attempt + 1 >= config.max_attempts:
                break
            
            # Calculate delay before next retry
            delay = config.calculate_delay(attempt)
            
            # Call retry callback if provided
            if on_retry:
                on_retry(attempt + 1, e, delay)
            
            logger.info(
                "Retrying database connection in %.2f seconds...",
                delay,
            )
            
            # Close the connection to force a fresh attempt
            conn = connections[database]
            conn.close()
            
            # Wait before retrying
            time.sleep(delay)
    
    # All retries exhausted
    total_time = time.time() - start_time
    
    raise DatabaseRetryExhaustedError(
        f"Failed to connect to database '{database}' after {config.max_attempts} attempts",
        max_attempts=config.max_attempts,
        total_time=total_time,
        last_error=last_error,
    )


def with_db_retry(
    config: Optional[DatabaseRetryConfig] = None,
    database: str = 'default',
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
):
    """
    Decorator that adds database retry logic to a function.
    
    This decorator implements the Retry Pattern, automatically
    retrying the decorated function on transient database failures.
    
    Args:
        config: Retry configuration (uses default if not provided)
        database: The database alias to use
        on_retry: Optional callback called on each retry
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @with_db_retry()
        def fetch_data():
            return MyModel.objects.filter(active=True)
        
        # With custom configuration
        @with_db_retry(config=DatabaseRetryConfig(max_attempts=10))
        def critical_operation():
            # Critical database operation
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return execute_with_retry(
                lambda: func(*args, **kwargs),
                config=config,
                database=database,
                on_retry=on_retry,
            )
        return wrapper
    return decorator


class DatabaseConnectionManager:
    """
    Context manager for database operations with retry support.
    
    This class provides a context manager interface for executing
    database operations with automatic retry on connection failures.
    
    Example:
        with DatabaseConnectionManager() as db:
            result = db.execute(lambda: User.objects.count())
        
        # With custom configuration
        config = DatabaseRetryConfig(max_attempts=3)
        with DatabaseConnectionManager(config=config) as db:
            db.execute(lambda: MyModel.objects.create(name='test'))
    """
    
    def __init__(
        self,
        config: Optional[DatabaseRetryConfig] = None,
        database: str = 'default',
    ):
        self.config = config or get_retry_config()
        self.database = database
        self._connection = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Don't suppress exceptions
        return False
    
    def execute(
        self,
        func: Callable,
        on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    ) -> any:
        """
        Execute a function with retry logic.
        
        Args:
            func: The function to execute
            on_retry: Optional callback for retry events
            
        Returns:
            The return value of the function
        """
        return execute_with_retry(
            func,
            config=self.config,
            database=self.database,
            on_retry=on_retry,
        )
    
    def ensure_connection(self) -> bool:
        """
        Ensure a database connection is available.
        
        Returns:
            True if connection is successful
            
        Raises:
            DatabaseRetryExhaustedError: If connection cannot be established
        """
        def check_connection():
            conn = connections[self.database]
            conn.ensure_connection()
            return True
        
        return execute_with_retry(
            check_connection,
            config=self.config,
            database=self.database,
        )
