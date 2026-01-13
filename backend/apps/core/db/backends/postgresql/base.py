"""
PostgreSQL database backend with automatic retry support.

This backend extends Django's PostgreSQL backend to add automatic
retry logic with exponential backoff for connection failures.
"""
import logging
import time
from typing import Optional

from django.db.backends.postgresql import base as postgresql_base
from django.db import OperationalError, InterfaceError

from apps.core.db.retry import get_retry_config, DatabaseRetryConfig
from apps.core.db.exceptions import DatabaseRetryExhaustedError

logger = logging.getLogger(__name__)


class RetryMixin:
    """
    Mixin that adds retry logic to database backend connections.
    
    This mixin overrides the get_new_connection and ensure_connection
    methods to add automatic retry with exponential backoff.
    """
    
    retry_config: Optional[DatabaseRetryConfig] = None
    
    def ensure_connection(self):
        """
        Ensure a database connection is available with retry logic.
        
        This method wraps the parent's ensure_connection to add
        automatic retry on connection failures.
        """
        if self.retry_config is None:
            self.retry_config = get_retry_config()
        
        last_error = None
        start_time = time.time()
        
        for attempt in range(self.retry_config.max_attempts):
            try:
                # Try to ensure connection using parent method
                super().ensure_connection()
                
                if attempt > 0:
                    logger.info(
                        "Database connection ensured after %d attempts",
                        attempt + 1,
                    )
                
                return
                
            except (OperationalError, InterfaceError) as e:
                last_error = e
                
                logger.warning(
                    "Database connection ensure attempt %d/%d failed: %s",
                    attempt + 1,
                    self.retry_config.max_attempts,
                    str(e),
                )
                
                if attempt + 1 >= self.retry_config.max_attempts:
                    break
                
                # Close any partial connection
                if hasattr(self, 'connection') and self.connection:
                    try:
                        self.connection.close()
                    except Exception:
                        pass
                
                delay = self.retry_config.calculate_delay(attempt)
                
                logger.info(
                    "Retrying database connection in %.2f seconds...",
                    delay,
                )
                
                time.sleep(delay)
        
        # All retries exhausted
        total_time = time.time() - start_time
        
        raise DatabaseRetryExhaustedError(
            f"Failed to ensure database connection after {self.retry_config.max_attempts} attempts",
            max_attempts=self.retry_config.max_attempts,
            total_time=total_time,
            last_error=last_error,
        )
    
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
                
            except (OperationalError, InterfaceError) as e:
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


class DatabaseWrapper(RetryMixin, postgresql_base.DatabaseWrapper):
    """
    PostgreSQL database backend with automatic retry support.
    
    This backend extends Django's PostgreSQL backend to automatically
    retry connection attempts with exponential backoff when the database
    is temporarily unavailable.
    
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
