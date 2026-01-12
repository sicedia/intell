"""
Database health check utilities.

This module provides health check functionality for database connections,
following the Health Check Pattern commonly used in microservices and
container orchestration systems.

The health checks are designed to be used with:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring systems
- Django management commands
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Dict, Any

from django.db import connection, connections, OperationalError

logger = logging.getLogger(__name__)


class DatabaseHealthStatus(Enum):
    """
    Enumeration of possible database health states.
    
    These states follow the standard health check conventions:
    - HEALTHY: Database is fully operational
    - UNHEALTHY: Database connection failed
    - DEGRADED: Database is operational but with issues
    - UNKNOWN: Health status could not be determined
    """
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class DatabaseHealthResult:
    """
    Result of a database health check.
    
    Attributes:
        status: The health status
        message: Human-readable status message
        response_time_ms: Database response time in milliseconds
        database_alias: The database connection alias checked
        details: Additional diagnostic information
    """
    status: DatabaseHealthStatus
    message: str
    response_time_ms: Optional[float] = None
    database_alias: str = 'default'
    details: Optional[Dict[str, Any]] = None
    
    def is_healthy(self) -> bool:
        """Check if the database is healthy."""
        return self.status == DatabaseHealthStatus.HEALTHY
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        result = {
            'status': self.status.value,
            'message': self.message,
            'database': self.database_alias,
        }
        if self.response_time_ms is not None:
            result['response_time_ms'] = round(self.response_time_ms, 2)
        if self.details:
            result['details'] = self.details
        return result


def check_database_connection(
    database: str = 'default',
    timeout: float = 5.0,
) -> Tuple[bool, str]:
    """
    Check if the database connection is healthy.
    
    This is a simple health check that attempts to execute a 
    basic query against the database.
    
    Args:
        database: The database alias to check (default: 'default')
        timeout: Maximum time to wait for the check in seconds
        
    Returns:
        Tuple of (is_healthy: bool, message: str)
        
    Example:
        is_healthy, message = check_database_connection()
        if not is_healthy:
            logger.error(f"Database unhealthy: {message}")
    """
    result = get_database_status(database=database, timeout=timeout)
    return result.is_healthy(), result.message


def get_database_status(
    database: str = 'default',
    timeout: float = 5.0,
    include_details: bool = False,
) -> DatabaseHealthResult:
    """
    Get detailed database health status.
    
    This function performs a comprehensive health check including:
    - Connection availability
    - Query execution time
    - Optional detailed diagnostics
    
    Args:
        database: The database alias to check
        timeout: Maximum time to wait for the check
        include_details: Whether to include detailed diagnostics
        
    Returns:
        DatabaseHealthResult with status and details
        
    Example:
        status = get_database_status(include_details=True)
        if not status.is_healthy():
            alert_ops_team(status.to_dict())
    """
    start_time = time.time()
    
    try:
        conn = connections[database]
        
        # Ensure we have a connection
        conn.ensure_connection()
        
        # Execute a simple query to verify the connection works
        with conn.cursor() as cursor:
            # Use a database-agnostic query
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Build result
        details = None
        if include_details:
            details = _get_connection_details(conn)
        
        # Check if response time indicates degraded performance
        if elapsed_ms > (timeout * 1000 * 0.8):  # 80% of timeout
            return DatabaseHealthResult(
                status=DatabaseHealthStatus.DEGRADED,
                message=f"Database responding slowly ({elapsed_ms:.0f}ms)",
                response_time_ms=elapsed_ms,
                database_alias=database,
                details=details,
            )
        
        return DatabaseHealthResult(
            status=DatabaseHealthStatus.HEALTHY,
            message="Database connection successful",
            response_time_ms=elapsed_ms,
            database_alias=database,
            details=details,
        )
        
    except OperationalError as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error("Database health check failed: %s", str(e))
        
        return DatabaseHealthResult(
            status=DatabaseHealthStatus.UNHEALTHY,
            message=f"Database connection failed: {str(e)}",
            response_time_ms=elapsed_ms,
            database_alias=database,
            details={'error_type': type(e).__name__, 'error': str(e)},
        )
        
    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.exception("Unexpected error during database health check")
        
        return DatabaseHealthResult(
            status=DatabaseHealthStatus.UNKNOWN,
            message=f"Health check error: {str(e)}",
            response_time_ms=elapsed_ms,
            database_alias=database,
            details={'error_type': type(e).__name__, 'error': str(e)},
        )


def _get_connection_details(conn) -> Dict[str, Any]:
    """
    Get detailed information about a database connection.
    
    Args:
        conn: Django database connection object
        
    Returns:
        Dictionary with connection details
    """
    details = {
        'vendor': conn.vendor,
        'alias': conn.alias,
    }
    
    # Add settings info (sanitized - no passwords)
    settings_info = conn.settings_dict.copy()
    if 'PASSWORD' in settings_info:
        settings_info['PASSWORD'] = '***'
    
    details['settings'] = {
        'engine': settings_info.get('ENGINE', 'unknown'),
        'name': settings_info.get('NAME', 'unknown'),
        'host': settings_info.get('HOST', 'localhost'),
        'port': settings_info.get('PORT', 'default'),
    }
    
    return details


def check_all_databases(
    include_details: bool = False,
) -> Dict[str, DatabaseHealthResult]:
    """
    Check health of all configured databases.
    
    Args:
        include_details: Whether to include detailed diagnostics
        
    Returns:
        Dictionary mapping database alias to health result
        
    Example:
        results = check_all_databases()
        unhealthy = [db for db, r in results.items() if not r.is_healthy()]
        if unhealthy:
            raise SystemError(f"Unhealthy databases: {unhealthy}")
    """
    results = {}
    
    for alias in connections:
        results[alias] = get_database_status(
            database=alias,
            include_details=include_details,
        )
    
    return results


def wait_for_database(
    database: str = 'default',
    timeout: float = 60.0,
    check_interval: float = 1.0,
) -> bool:
    """
    Wait for the database to become available.
    
    This function is useful for startup scenarios where the database
    might not be immediately available (e.g., in containerized environments).
    
    Args:
        database: The database alias to wait for
        timeout: Maximum time to wait in seconds
        check_interval: Time between checks in seconds
        
    Returns:
        True if database became available, False if timeout occurred
        
    Example:
        # In a startup script or AppConfig.ready()
        if not wait_for_database(timeout=30):
            raise RuntimeError("Database not available")
    """
    start_time = time.time()
    
    while (time.time() - start_time) < timeout:
        is_healthy, message = check_database_connection(
            database=database,
            timeout=check_interval,
        )
        
        if is_healthy:
            logger.info("Database '%s' is available", database)
            return True
        
        logger.info(
            "Waiting for database '%s'... (%s)",
            database,
            message,
        )
        time.sleep(check_interval)
    
    logger.error(
        "Timeout waiting for database '%s' after %.1f seconds",
        database,
        timeout,
    )
    return False
