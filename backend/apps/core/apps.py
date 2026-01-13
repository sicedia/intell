"""
App configuration for the core app.

This AppConfig ensures database connectivity after Django is fully initialized,
using the retry mechanism to handle transient connection failures during
server startup. The check is deferred to avoid accessing the database during
app initialization, which Django discourages.
"""
import logging
import threading
from django.apps import AppConfig
from django.conf import settings

logger = logging.getLogger(__name__)


def _check_database_connection():
    """
    Check database connection in a separate thread after Django is ready.
    
    This function is called after a short delay to ensure Django is
    completely initialized before accessing the database.
    """
    # Verify Django is fully ready before accessing database
    from django.apps import apps
    if not apps.ready:
        logger.debug("Django apps not ready yet, skipping database check")
        return
    
    # Only wait for database in non-testing environments
    # and if DATABASE_WAIT_ON_STARTUP is enabled
    wait_on_startup = getattr(settings, 'DATABASE_WAIT_ON_STARTUP', True)
    
    if not wait_on_startup or getattr(settings, 'TESTING', False):
        return
    
    try:
        from .db import wait_for_database
        
        # Get timeout from settings or use default
        timeout = getattr(settings, 'DATABASE_STARTUP_TIMEOUT', 30.0)
        check_interval = getattr(settings, 'DATABASE_STARTUP_CHECK_INTERVAL', 2.0)
        
        logger.info(
            "Waiting for database connection (timeout: %.1fs)...",
            timeout
        )
        
        # Wait for database with retry
        database_available = wait_for_database(
            database='default',
            timeout=timeout,
            check_interval=check_interval,
        )
        
        if database_available:
            logger.info("Database connection established successfully")
        else:
            logger.warning(
                "Database not available after %.1fs. "
                "Server will start but database operations may fail.",
                timeout
            )
            
    except ImportError:
        # If db module is not available, log warning but don't fail
        logger.warning(
            "Database retry module not available. "
            "Skipping startup database check."
        )
    except Exception as e:
        # Log error but don't prevent server startup
        # This allows the server to start even if database check fails
        logger.error(
            "Error during database startup check: %s",
            str(e),
            exc_info=True
        )


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    
    def ready(self):
        """
        Called when Django starts.
        
        This method schedules a database connectivity check to run
        after Django is fully initialized, avoiding the warning about
        accessing the database during app initialization.
        """
        def delayed_check():
            """
            Wait for Django to be fully ready before checking database.
            
            This function polls django.apps.apps.ready to ensure Django
            is completely initialized before accessing the database.
            """
            import time
            from django.apps import apps
            
            # Wait for Django to be fully ready (max 5 seconds)
            max_wait = 5.0
            wait_interval = 0.1
            elapsed = 0.0
            
            while not apps.ready and elapsed < max_wait:
                time.sleep(wait_interval)
                elapsed += wait_interval
            
            if not apps.ready:
                logger.warning(
                    "Django apps not ready after %.1fs, skipping database check",
                    max_wait
                )
                return
            
            # Now that Django is ready, check the database
            _check_database_connection()
        
        # Run in a daemon thread so it doesn't prevent server shutdown
        thread = threading.Thread(target=delayed_check, daemon=True)
        thread.start()

