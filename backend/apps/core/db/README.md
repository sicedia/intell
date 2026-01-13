# Database Module

This module provides robust database connection handling with automatic retry logic for the Intelli project.

## Features

- **Automatic Retry with Exponential Backoff**: Implements the industry-standard retry pattern to handle transient database connection failures
- **Configurable Retry Policy**: All retry parameters can be configured via Django settings or environment variables
- **Health Check Endpoints**: REST API endpoints and management commands for monitoring database health
- **Custom Database Backends**: Drop-in replacements for Django's database backends with built-in retry support
- **Clean Error Handling**: Specific exception types for different database error scenarios

## Architecture

```
apps/core/db/
├── __init__.py          # Public API exports
├── backends/            # Custom database backends with retry
│   ├── __init__.py
│   ├── postgresql/      # PostgreSQL backend with retry
│   │   ├── __init__.py
│   │   └── base.py      # DatabaseWrapper with retry logic
│   └── sqlite3/         # SQLite backend with retry
│       ├── __init__.py
│       └── base.py      # DatabaseWrapper with retry logic
├── exceptions.py        # Database-specific exceptions
├── health.py            # Health check utilities
├── retry.py             # Core retry logic with exponential backoff
└── README.md            # This file
```

## Usage

### 1. Using the Retry Decorator

For functions that perform database operations:

```python
from apps.core.db import with_db_retry

@with_db_retry()
def fetch_user_data(user_id):
    return User.objects.get(id=user_id)

# With custom configuration
from apps.core.db import with_db_retry, DatabaseRetryConfig

config = DatabaseRetryConfig(
    max_attempts=10,
    initial_delay=0.5,
    max_delay=60.0,
)

@with_db_retry(config=config)
def critical_operation():
    # Important database operation
    pass
```

### 2. Using the Context Manager

For more control over retry behavior:

```python
from apps.core.db.retry import DatabaseConnectionManager

with DatabaseConnectionManager() as db:
    result = db.execute(lambda: User.objects.count())
```

### 3. Using Custom Database Backends (Optional)

For automatic retry on all database connections, update your `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'apps.core.db.backends.postgresql',  # Instead of django.db.backends.postgresql
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'mypassword',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 4. Health Checks

#### REST API Endpoint

```bash
# Basic health check
curl http://localhost:8000/api/health/database/

# With detailed information
curl http://localhost:8000/api/health/database/?details=true

# Check specific database
curl http://localhost:8000/api/health/database/?database=replica
```

#### Management Command

```bash
# Basic check
python manage.py check_db

# Wait for database (useful for Docker/Kubernetes)
python manage.py check_db --wait --timeout 60

# Check with verbose output
python manage.py check_db --verbose

# Check all databases
python manage.py check_db --all
```

#### Programmatic Health Check

```python
from apps.core.db import check_database_connection, get_database_status

# Simple check
is_healthy, message = check_database_connection()
if not is_healthy:
    logger.error(f"Database unhealthy: {message}")

# Detailed status
status = get_database_status(include_details=True)
if not status.is_healthy():
    send_alert(status.to_dict())
```

## Configuration

Configure retry behavior in `settings.py` or via environment variables:

```python
# settings.py
DATABASE_RETRY_CONFIG = {
    'MAX_ATTEMPTS': 5,          # Maximum retry attempts
    'INITIAL_DELAY': 0.1,       # Initial delay in seconds
    'MAX_DELAY': 30.0,          # Maximum delay cap
    'EXPONENTIAL_BASE': 2.0,    # Backoff multiplier
    'JITTER': True,             # Add random jitter
    'JITTER_FACTOR': 0.1,       # Jitter range (±10%)
}
```

Environment variables:
- `DB_RETRY_MAX_ATTEMPTS`
- `DB_RETRY_INITIAL_DELAY`
- `DB_RETRY_MAX_DELAY`
- `DB_RETRY_EXPONENTIAL_BASE`
- `DB_RETRY_JITTER`
- `DB_RETRY_JITTER_FACTOR`

## Retry Pattern

The module implements **Exponential Backoff with Jitter**:

1. **Exponential Backoff**: Each retry waits longer than the previous one
   - Delay = min(MAX_DELAY, INITIAL_DELAY × EXPONENTIAL_BASE^attempt)

2. **Jitter**: Random variation prevents synchronized retries (thundering herd)
   - Final delay = delay ± (delay × JITTER_FACTOR)

Default retry timeline:
| Attempt | Base Delay | With Jitter (±10%) |
|---------|------------|-------------------|
| 1       | 0.1s       | 0.09s - 0.11s    |
| 2       | 0.2s       | 0.18s - 0.22s    |
| 3       | 0.4s       | 0.36s - 0.44s    |
| 4       | 0.8s       | 0.72s - 0.88s    |
| 5       | 1.6s       | 1.44s - 1.76s    |

## Exception Handling

```python
from apps.core.db import (
    DatabaseConnectionError,
    DatabaseRetryExhaustedError,
)
from apps.core.db.exceptions import (
    DatabaseQueryError,
    DatabaseTimeoutError,
)

try:
    result = execute_with_retry(my_operation)
except DatabaseRetryExhaustedError as e:
    logger.error(f"All retries failed: {e}")
    logger.error(f"Attempts: {e.max_attempts}, Time: {e.total_time}s")
    raise
```

## Best Practices

1. **Use for transient failures only**: This pattern is designed for temporary issues like network hiccups or database restarts. Persistent errors (wrong credentials, missing tables) will still fail after all retries.

2. **Configure appropriately for your environment**:
   - Development: Lower attempts, shorter delays
   - Production: More attempts, longer delays
   - Kubernetes: Use `check_db --wait` in init containers

3. **Monitor retry metrics**: Log retry attempts to track database reliability.

4. **Combine with circuit breaker**: For high-traffic applications, consider adding a circuit breaker pattern to prevent cascade failures.

## Integration with Kubernetes

Example Kubernetes deployment with startup probe:

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      initContainers:
        - name: wait-for-db
          image: your-django-image
          command: ['python', 'manage.py', 'check_db', '--wait', '--timeout', '60']
      containers:
        - name: django
          livenessProbe:
            httpGet:
              path: /api/health/database/
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /api/health/database/
              port: 8000
            initialDelaySeconds: 3
            periodSeconds: 5
```

## References

- [AWS Architecture Blog: Exponential Backoff and Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [Django Database Configuration](https://docs.djangoproject.com/en/stable/ref/databases/)
- [Microsoft Azure: Retry Pattern](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)
