"""
Custom database backends with retry support.

This module provides database backend wrappers that add automatic
retry logic to database connections. These backends can be used
as drop-in replacements for Django's standard database backends.

Usage in settings.py:
    DATABASES = {
        'default': {
            'ENGINE': 'apps.core.db.backends.postgresql',
            # ... other settings
        }
    }

The backends intercept connection failures and automatically retry
using exponential backoff, making your application more resilient
to transient database issues.
"""

import logging
import time
from typing import Optional

from django.db.backends.postgresql import base as postgresql_base
from django.db.backends.sqlite3 import base as sqlite3_base
from django.db import OperationalError

from .retry import get_retry_config, DatabaseRetryConfig
from .exceptions import DatabaseRetryExhaustedError

logger = logging.getLogger(__name__)


class RetryMixin:
    """
    Mixin that adds retry logic to database backend connections.
    
    This mixin overrides the get_new_connection method to add
    automatic retry with exponential backoff.
    """
    
    retry_config: Optional[DatabaseRetryConfig] = None
    
    def get_new_connection(self, conn_params):
        """
        Get a new database connection with retry logic.
        
        This method wraps the parent's get_new_connection method
        and adds automatic retry on connection failures.
        """
        if self.retry_config is None:
            self.retry_config = get_retry_config()
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                connection = super().get_new_connection(conn_params)
                
                if attempt > 0:
                    logger.info(
                        "Database connection established after %d attempts",
                        attempt + 1,
                    )
                
                return connection
                
            except OperationalError as e:
                last_error = e
                
                logger.warning(
                    "Database connection attempt %d/%d failed: %s",
                    attempt + 1,
                    self.retry_config.max_attempts,
                    str(e),
                )
                
                if attempt + 1 >= self.retry_config.max_attempts:
                    break
                
                delay = self.retry_config.calculate_delay(attempt)
                
                logger.info(
                    "Retrying database connection in %.2f seconds...",
                    delay,
                )
                
                time.sleep(delay)
        
        # All retries exhausted
        total_time = time.time() - start_time
        
        raise DatabaseRetryExhaustedError(
            f"Failed to establish database connection after {self.retry_config.max_attempts} attempts",
            max_attempts=self.retry_config.max_attempts,
            total_time=total_time,
            last_error=last_error,
        )


class PostgreSQLDatabaseWrapper(RetryMixin, postgresql_base.DatabaseWrapper):
    """
    PostgreSQL database backend with automatic retry support.
    
    Use this backend in your settings.py:
        DATABASES = {
            'default': {
                'ENGINE': 'apps.core.db.backends.postgresql',
                'NAME': 'mydb',
                'USER': 'myuser',
                'PASSWORD': 'mypassword',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
    """
    pass


class SQLiteDatabaseWrapper(RetryMixin, sqlite3_base.DatabaseWrapper):
    """
    SQLite database backend with automatic retry support.
    
    While SQLite rarely has connection issues, this backend can
    help with file locking issues in high-concurrency scenarios.
    
    Use this backend in your settings.py:
        DATABASES = {
            'default': {
                'ENGINE': 'apps.core.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
    """
    pass


# Backend modules for Django to import
# These follow Django's convention for database backends

class postgresql:
    """PostgreSQL backend module with retry support."""
    DatabaseWrapper = PostgreSQLDatabaseWrapper


class sqlite3:
    """SQLite backend module with retry support."""
    DatabaseWrapper = SQLiteDatabaseWrapper
