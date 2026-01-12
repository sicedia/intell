"""
Database module for the Intelli project.

This module provides robust database connection handling with:
- Automatic retry with exponential backoff
- Connection health checks
- Custom database backends with retry support
- Configurable retry policies

Usage:
    # Using the retry decorator for database operations
    from apps.core.db import with_db_retry, DatabaseRetryConfig
    
    @with_db_retry()
    def my_database_operation():
        # Your database code here
        pass
    
    # Using health check
    from apps.core.db import check_database_connection
    
    is_healthy, message = check_database_connection()
"""

from .retry import (
    with_db_retry,
    DatabaseRetryConfig,
    execute_with_retry,
    get_retry_config,
)
from .health import (
    check_database_connection,
    get_database_status,
    wait_for_database,
    DatabaseHealthStatus,
)
from .exceptions import (
    DatabaseConnectionError,
    DatabaseRetryExhaustedError,
)

__all__ = [
    # Retry utilities
    'with_db_retry',
    'DatabaseRetryConfig',
    'execute_with_retry',
    'get_retry_config',
    # Health checks
    'check_database_connection',
    'get_database_status',
    'wait_for_database',
    'DatabaseHealthStatus',
    # Exceptions
    'DatabaseConnectionError',
    'DatabaseRetryExhaustedError',
]
