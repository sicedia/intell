# Celery & Redis Setup Guide

This document explains the Celery and Redis configuration for the Intelli backend.

## Current Configuration

### ✅ EAGER Mode Disabled

The `CELERY_TASK_ALWAYS_EAGER` setting has been **disabled** in `config/settings/development.py`. This means:

- ✅ Tasks will be processed asynchronously via Redis
- ✅ Multiple tasks can run in parallel
- ✅ API responses return immediately (non-blocking)
- ⚠️ **You must run Celery workers** for tasks to be processed

### Redis Configuration

Redis is used for two purposes:

1. **Celery Broker** (DB 0): Queues tasks for workers
2. **Celery Result Backend** (DB 0): Stores task results
3. **Django Channels** (DB 1): WebSocket channel layer for real-time updates

Configuration in `.env`:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/1
```

## Running Celery Workers

### Quick Start

**Windows PowerShell:**
```powershell
cd backend
.\scripts\start_celery_worker.ps1
```

**Linux/macOS:**
```bash
cd backend
chmod +x scripts/start_celery_worker.sh
./scripts/start_celery_worker.sh
```

**Important for Windows:** The configuration in `config/celery.py` automatically detects Windows and uses the `solo` pool. On Linux/macOS (production), the `prefork` pool is used by default for better parallel performance. The `prefork` pool doesn't work on Windows due to process forking limitations.

### Manual Start

Start a single worker for all queues:
```bash
cd backend
celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
```

**Note:** The pool type is automatically selected:
- **Windows**: Uses `solo` pool (sequential execution)
- **Linux/macOS**: Uses `prefork` pool (parallel execution) - **Recommended for production**

### Separate Workers (Recommended for Production)

For better isolation and resource management, run separate workers:

**Terminal 1 - Ingestion I/O:**
```bash
celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4 -l info
```

**Terminal 2 - Charts CPU:**
```bash
celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1 -l info
```

**Terminal 3 - AI:**
```bash
celery -A config worker -Q ai -c 2 --prefetch-multiplier=1 -l info
```

## Verification

### Check Celery Setup

```bash
cd backend
python scripts/check_celery.py
```

This verifies:
- ✅ Redis connectivity (broker and channels)
- ✅ EAGER mode is disabled
- ✅ Celery workers are running
- ✅ Tasks are registered

### Check WebSocket Setup

```bash
cd backend
python scripts/test_websocket.py
```

This verifies:
- ✅ Django Channels configuration
- ✅ Redis Channels layer connectivity
- ✅ WebSocket URL routing
- ✅ Event emission works

## Queue Configuration

| Queue | Concurrency | Prefetch | acks_late | time_limit | Use Case |
|-------|-------------|----------|-----------|------------|----------|
| `ingestion_io` | 4 | 4 | False | 60s | I/O bound (HTTP, file reads) |
| `charts_cpu` | 2 | 1 | True | 120s | CPU bound (matplotlib, algorithms) |
| `ai` | 2 | 1 | True | 60s | I/O bound (API calls) + retries |

## Troubleshooting

### Workers Not Processing Tasks

1. **Check Redis is running:**
   ```bash
   docker exec infrastructure-redis-1 redis-cli ping
   ```
   Should return: `PONG`

2. **Check workers are running:**
   ```bash
   celery -A config inspect active
   ```

3. **Check EAGER mode is disabled:**
   ```bash
   grep CELERY_TASK_ALWAYS_EAGER backend/config/settings/development.py
   ```
   Should show commented lines (starting with `#`)

### WebSocket Not Connecting

1. **Check Redis Channels layer:**
   ```bash
   docker exec infrastructure-redis-1 redis-cli -n 1 ping
   ```

2. **Verify ASGI application:**
   - Ensure `daphne` is installed: `pip install daphne`
   - Run with: `daphne -b 0.0.0.0 -p 8000 config.asgi:application`
   - Or use Django's runserver (supports WebSocket in development)

### Re-enabling EAGER Mode (Debugging Only)

If you need synchronous execution for debugging:

1. Edit `backend/config/settings/development.py`
2. Uncomment these lines:
   ```python
   CELERY_TASK_ALWAYS_EAGER = True
   CELERY_TASK_EAGER_PROPAGATES = True
   ```
3. Restart Django server

**Warning**: EAGER mode blocks API responses until all tasks complete. Only use for debugging.

## Development Workflow

### Typical Development Setup

1. **Start infrastructure:**
   ```bash
   cd infrastructure
   docker-compose up -d
   ```

2. **Start Django server:**
   ```bash
   cd backend
   python manage.py runserver
   ```

3. **Start Celery worker (new terminal):**
   ```bash
   cd backend
   .\scripts\start_celery_worker.ps1  # Windows
   # or
   ./scripts/start_celery_worker.sh  # Linux/macOS
   ```

4. **Start frontend (new terminal):**
   ```bash
   cd frontend
   npm run dev
   ```

### Monitoring

**Flower** (optional Celery monitoring):
```bash
celery -A config flower
```
Access at: http://localhost:5555

## Architecture Flow

```
Frontend → POST /api/jobs/ → Django API
                              ↓
                         Create Job + ImageTasks
                              ↓
                         Enqueue tasks to Redis
                              ↓
                    Celery Worker picks up tasks
                              ↓
                    Execute algorithms in parallel
                              ↓
                    Save artifacts + emit events
                              ↓
                    WebSocket → Frontend (real-time)
```

## Best Practices

1. **Always run workers in development** - Don't rely on EAGER mode
2. **Monitor worker logs** - Check for errors and performance
3. **Use separate queues** - Better resource management
4. **Test WebSocket** - Verify real-time updates work
5. **Check Redis health** - Ensure Redis is running and accessible

## Related Files

- `backend/config/settings/development.py` - Celery configuration
- `backend/config/celery.py` - Celery app setup and queue routing
- `backend/apps/jobs/tasks.py` - Task definitions
- `backend/scripts/check_celery.py` - Verification script
- `backend/scripts/test_websocket.py` - WebSocket test script
- `backend/scripts/start_celery_worker.ps1` - Windows startup script
- `backend/scripts/start_celery_worker.sh` - Linux/macOS startup script
