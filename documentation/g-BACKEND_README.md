# Intelli Backend

Django + DRF + Celery + Redis + Channels + PostgreSQL backend for patent data processing and chart generation.

## Architecture

The backend follows a canonical Dataset pipeline:

```
Excel/API → normalize() → Dataset → Job → ImageTask → Algorithm → PNG/SVG
                                      ↓
                              WebSocket Events → Frontend
```

Key principles:
- All algorithms consume `datasets.Dataset` (never raw data)
- EventLog is append-only with `emit_event()` as the single source of truth
- Individual task retry/cancel without affecting other tasks
- Automatic job status calculation when all tasks complete

## Project Structure

```
backend/
├── apps/
│   ├── core/              # Health checks, shared utilities
│   ├── ingestion/         # Data source connectors (Lens API)
│   ├── datasets/          # Canonical dataset normalization
│   ├── algorithms/        # Chart generation algorithms
│   │   └── demo/          # Patent chart algorithms
│   ├── jobs/              # Job orchestration, tasks, WebSocket
│   │   ├── models.py      # Job, ImageTask, DescriptionTask
│   │   ├── views.py       # REST API (create, retry, cancel)
│   │   ├── tasks.py       # Celery tasks
│   │   ├── consumers.py   # WebSocket consumer
│   │   └── serializers.py # DRF serializers
│   ├── artifacts/         # Artifact storage
│   ├── ai_descriptions/   # AI-powered chart descriptions
│   └── audit/             # Append-only event logging
├── config/
│   ├── settings/          # Environment-specific settings
│   │   ├── base.py        # Shared settings
│   │   ├── development.py # Development (DEBUG=True)
│   │   └── production.py  # Production (security, PostgreSQL)
│   ├── celery.py          # Celery configuration (auto pool detection)
│   └── asgi.py            # ASGI config (Daphne + Channels)
├── scripts/               # Utility scripts
├── context/               # Test data and examples
├── media/                 # Generated artifacts (PNG/SVG)
├── Dockerfile.prod        # Production Dockerfile
├── pyproject.toml         # Poetry dependencies
└── poetry.lock            # Poetry lock file
```

## Setup

### Prerequisites

- Python 3.12+ (required for Django 6.0)
- Poetry (for dependency management)
- Docker and Docker Compose (for PostgreSQL and Redis)

### Installation

#### Automated Setup (Recommended)

1. **Start infrastructure services:**
   ```bash
   cd ../infrastructure
   # Use automated setup script
   ./setup.sh  # Linux/macOS
   # or
   .\setup.ps1  # Windows PowerShell
   
   # Or manually:
   docker-compose up -d
   ```

2. **Install Python dependencies:**
   ```bash
   cd ../backend
   # Install Poetry if not already installed
   pip install poetry
   
   # Install all dependencies
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp env.development.example .env
   # The DATABASE_URL is already configured in env.example
   ```

4. **Run automated backend setup:**
   ```bash
   poetry run python scripts/setup_dev.py
   ```
   
   This script will:
   - Check if infrastructure services are running
   - Wait for database to be ready
   - Run Django migrations automatically
   - Create a superuser interactively (optional)
   
   Options:
   ```bash
   poetry run python scripts/setup_dev.py --skip-superuser  # Skip superuser creation
   poetry run python scripts/setup_dev.py --skip-infrastructure-check  # Skip infrastructure check
   ```

#### Manual Setup (Alternative)

If you prefer to set up manually:

1. **Start infrastructure services:**
   ```bash
   cd ../infrastructure
   docker-compose up -d
   ```

2. **Install Python dependencies:**
   ```bash
   cd ../backend
   # Install Poetry if not already installed
   pip install poetry
   
   # Install all dependencies
   poetry install
   ```

3. **Set up environment variables:**
   ```bash
   cp env.development.example .env
   ```
   
   **Required variables for development:**
   ```bash
   DATABASE_URL=postgresql://intell_user:patents2026$@localhost:5432/intell
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   REDIS_URL=redis://localhost:6379/1
   ```

4. **Verify infrastructure connectivity:**
   ```bash
   poetry run python scripts/check_infrastructure.py
   ```

5. **Run migrations:**
   ```bash
   poetry run python manage.py makemigrations
   poetry run python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   poetry run python manage.py createsuperuser
   ```

## Running the Application

### Django Server

**Using Poetry shell:**
```bash
cd backend
poetry shell
python manage.py runserver
```

**Or using poetry run:**
```bash
cd backend
poetry run python manage.py runserver
```

Server runs at `http://localhost:8000`

### Celery Workers

**Important**: EAGER mode is disabled by default. You must run Celery workers for tasks to be processed asynchronously.

#### Quick Start (Recommended)

Use the helper script to start all queues in one worker:

**Windows PowerShell:**
```powershell
cd backend
poetry shell
.\scripts\start_celery_worker.ps1
```

**Linux/macOS:**
```bash
cd backend
poetry shell
chmod +x scripts/start_celery_worker.sh
./scripts/start_celery_worker.sh
```

This starts a single worker processing all queues: `ingestion_io`, `charts_cpu`, and `ai`.

**Automatic Pool Detection:** The configuration in `config/celery.py` automatically detects the OS:
- **Windows**: Uses `solo` pool (sequential execution, for development)
- **Linux/macOS**: Uses `prefork` pool (parallel execution, for production)

For better performance on Windows development, consider using WSL2 or Docker.

#### Manual Start

Start a single worker for all queues:
```bash
poetry run celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
```

Or run separate workers for better isolation:

**Terminal 1 - Ingestion I/O queue:**
```bash
poetry run celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4 -l info
```

**Terminal 2 - Charts CPU queue:**
```bash
poetry run celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1 -l info
```

**Terminal 3 - AI queue:**
```bash
poetry run celery -A config worker -Q ai -c 2 --prefetch-multiplier=1 -l info
```

#### Verify Celery Setup

Check that Redis is accessible and workers are running:
```bash
poetry run python scripts/check_celery.py
```

This script verifies:
- ✅ Redis connectivity (broker and channels)
- ✅ EAGER mode is disabled
- ✅ Celery workers are running
- ✅ Tasks are registered

#### Enabling EAGER Mode (Debugging Only)

If you need synchronous task execution for debugging, uncomment these lines in `config/settings/development.py`:
```python
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

**Note**: EAGER mode defeats the async architecture and blocks API responses. Only use for debugging.

### Infrastructure Services (PostgreSQL and Redis)

Start via docker-compose:
```bash
cd ../infrastructure
docker-compose up -d
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379 (DB 0 for Celery, DB 1 for Channels)

Verify services are running:
```bash
# Check PostgreSQL
docker-compose exec db pg_isready -U intell_user

# Check Redis
docker-compose exec redis redis-cli ping
```

Or use the verification script:
```bash
poetry run python scripts/check_infrastructure.py
```

## API Endpoints

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | Basic health check |
| `/api/health/redis/` | GET | Redis connectivity check |
| `/api/health/celery/` | GET | Celery worker check |

### Jobs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs/` | POST | Create a new job |
| `/api/jobs/<id>/` | GET | Get job details with all tasks |
| `/api/jobs/<id>/cancel/` | POST | Cancel entire job |

### Image Tasks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/image-tasks/<id>/` | GET | Get image task details |
| `/api/image-tasks/<id>/retry/` | POST | Retry failed/stuck task |
| `/api/image-tasks/<id>/cancel/` | POST | Cancel running/pending task |

**Retry behavior:**
- Resets task to PENDING status
- Clears error information
- Re-enqueues task for processing
- Updates job status if needed (FAILED → RUNNING)
- Automatically updates job status when all tasks complete

**Cancel behavior:**
- Only for PENDING or RUNNING tasks
- Marks task as CANCELLED
- Updates job status if all tasks cancelled

### AI Descriptions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/describe/` | POST | Create AI description task |

### API Documentation

| Endpoint | Description |
|----------|-------------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc UI |
| `/api/schema/` | OpenAPI schema |

## Example Requests

### Create Job with Excel File

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -F "source_type=espacenet_excel" \
  -F "source_data=@context/Filters_20250522_1212.xlsx" \
  -F 'images=[{"algorithm_key":"top_patent_countries","algorithm_version":"1.0","params":{"top_n":15},"output_format":"both"}]' \
  -F "idempotency_key=test-key-123"
```

Response:
```json
{
  "job_id": 1,
  "status": "PENDING",
  "message": "Job created and enqueued"
}
```

### Get Job Details

```bash
curl http://localhost:8000/api/jobs/1/
```

Response:
```json
{
  "id": 1,
  "status": "SUCCESS",
  "progress_total": 100,
  "dataset_id": 1,
  "image_tasks": [
    {
      "id": 1,
      "algorithm_key": "top_patent_countries",
      "status": "SUCCESS",
      "artifact_png_url": "http://localhost:8000/media/artifacts/png/job_1/task_1.png",
      "artifact_svg_url": "http://localhost:8000/media/artifacts/svg/job_1/task_1.svg",
      "chart_data": {...}
    }
  ]
}
```

### Retry Failed Image Task

```bash
curl -X POST http://localhost:8000/api/image-tasks/1/retry/
```

Response:
```json
{
  "image_task_id": 1,
  "status": "PENDING",
  "message": "Task retry initiated",
  "task": {...}
}
```

### Cancel Running Image Task

```bash
curl -X POST http://localhost:8000/api/image-tasks/1/cancel/
```

Response:
```json
{
  "image_task_id": 1,
  "status": "CANCELLED",
  "message": "Task cancelled successfully",
  "task": {...}
}
```

### Create AI Description

```bash
curl -X POST http://localhost:8000/api/ai/describe/ \
  -H "Content-Type: application/json" \
  -d '{
    "image_task_id": 1,
    "user_context": "Describe this chart focusing on Ecuador"
  }'
```

Response:
```json
{
  "description_task_id": 1,
  "status": "PENDING",
  "message": "Description task created and enqueued"
}
```

## WebSocket

Connect to job progress WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/jobs/1/');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.event_type, data.message, data.progress);
};
```

### Event Types

| Event | Entity | Description |
|-------|--------|-------------|
| `START` | job/image_task | Task started |
| `PROGRESS` | job/image_task | Progress update (0-100) |
| `DONE` | job/image_task | Task completed successfully |
| `ERROR` | job/image_task | Task failed |
| `ALGORITHM_ERROR` | image_task | Algorithm execution failed |
| `CANCELLED` | job/image_task | Task was cancelled |
| `RETRY` | image_task | Task retry initiated |
| `job_status_changed` | job | Job status changed (SUCCESS, FAILED, etc.) |

### Event Payload Structure

```json
{
  "job_id": 1,
  "entity_type": "image_task",
  "entity_id": 1,
  "event_type": "PROGRESS",
  "level": "INFO",
  "progress": 50,
  "message": "Executing algorithm",
  "payload": {},
  "trace_id": "uuid-here",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Job Status Changed Event

When all tasks complete, emits:
```json
{
  "job_id": 1,
  "event_type": "job_status_changed",
  "progress": 100,
  "payload": {
    "status": "SUCCESS",
    "previous_status": "RUNNING"
  }
}
```

## Testing

The project uses **pytest** and **pytest-django** for testing. Tests are organized by app in `apps/*/tests/` and integration tests in `backend/tests/`.

### Running Tests

**Run all tests:**
```bash
poetry run pytest
```

**Run tests with migrations (required for integration tests):**
```bash
poetry run pytest --migrations
```

**Run specific test file:**
```bash
poetry run pytest apps/algorithms/tests/test_registry.py
```

**Run specific test:**
```bash
poetry run pytest apps/audit/tests/test_emit_event.py::TestEmitEvent::test_emit_event_for_job
```

**Run with coverage:**
```bash
poetry run pytest --cov=apps --cov-report=html
```

### Test Structure

- **Unit tests**: `apps/*/tests/` - Test individual components
- **Integration tests**: `backend/tests/` - Test complete pipelines
- **Fixtures**: `backend/tests/conftest.py` and `apps/*/tests/conftest.py`

### Test Examples

**Algorithm Registry:**
```bash
pytest apps/algorithms/tests/test_registry.py -v
```

**Event Logging:**
```bash
pytest apps/audit/tests/test_emit_event.py -v
```

**End-to-End Pipeline (requires migrations):**
```bash
pytest tests/test_end_to_end.py --migrations -v
```

### Legacy Django Test

The original Django unittest is still available:
```bash
python manage.py test apps.jobs.tests.JobPipelineTestCase
```

## Configuration

### Environment Variables

Key variables in `.env`:
- `SECRET_KEY`: Django secret key
- `DEBUG`: Debug mode (True/False)
- `DATABASE_URL`: PostgreSQL connection string
- `CELERY_BROKER_URL`: Redis URL for Celery
- `REDIS_URL`: Redis URL for Channels
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)

### Celery Queues

Three queues with different tuning:

| Queue | Concurrency | Prefetch | acks_late | time_limit | Use Case |
|-------|-------------|----------|-----------|------------|----------|
| `ingestion_io` | 4 | 4 | False | 60s | I/O bound (HTTP, file reads) |
| `charts_cpu` | 2 | 1 | True | 120s | CPU bound (matplotlib, algorithms) |
| `ai` | 2 | 1 | True | 60s | I/O bound (API calls) + retries |

## Admin Interface

Access admin at `http://localhost:8000/admin/`

- **Dataset**: View and manage canonical datasets
- **Job**: View and manage jobs
- **ImageTask**: View image tasks and artifacts
- **DescriptionTask**: View AI description tasks
- **EventLog**: Read-only event log (append-only)

## Key Concepts

### Dataset Canonical Format

All algorithms consume `datasets.Dataset`, never raw data. The Dataset model:
- Has `storage_path` pointing to normalized JSON/Parquet file
- Contains `summary_stats` and `columns_map`
- File must exist physically on disk

### EventLog Append-Only

- `EventLog` is append-only (only INSERTs, never UPDATEs)
- State changes occur in Job/ImageTask/DescriptionTask
- `emit_event()` is the single source of truth
- Always: insert EventLog → update status/progress → publish WebSocket

### Idempotency

Jobs support idempotency via `idempotency_key`:
- Scoped by `created_by` (if authenticated)
- Global if `created_by` is null
- Same key returns existing job

### Job Status Calculation

Job status is calculated automatically when all tasks complete:

| Condition | Status |
|-----------|--------|
| All tasks SUCCESS | `SUCCESS` |
| Some SUCCESS, some FAILED | `PARTIAL_SUCCESS` |
| All FAILED | `FAILED` |
| All CANCELLED | `CANCELLED` |

**Status update triggers:**
1. `finalize_job` - Called by Celery chord after initial job run
2. `_check_and_update_job_status` - Called after individual task completion (retry/error)

This ensures job status updates correctly even for:
- Individual task retries
- Tasks that fail after retry
- Mixed success/failure scenarios

## Troubleshooting

### Celery Workers Not Starting

Check Redis connection:
```bash
redis-cli ping
```

### WebSocket Not Connecting

Verify Channels configuration and Redis for channel layers.

### Algorithms Not Found

Register algorithms in code or via management command:
```python
from apps.algorithms.registry import AlgorithmRegistry
from apps.algorithms.demo.top_patent_countries import TopPatentCountriesAlgorithm

registry = AlgorithmRegistry()
registry.register("top_patent_countries", "1.0", TopPatentCountriesAlgorithm())
```

## Development

### Adding New Algorithms

1. Create algorithm class inheriting `BaseAlgorithm`
2. Implement `run(dataset: Dataset, params: dict) -> ChartResult`
3. Register in `AlgorithmRegistry`
4. Algorithm must read from `Dataset.storage_path`

### Adding New Data Sources

1. Create connector in `apps/ingestion/connectors.py`
2. Add normalizer in `apps/datasets/normalizers.py`
3. Update `Dataset.SOURCE_TYPE_CHOICES`

## Docker Production

### Dockerfile

The production Dockerfile (`Dockerfile.prod`) includes:
- Python 3.13 slim base
- Daphne ASGI server (WebSocket support)
- Health check endpoint
- Non-root user for security
- Static files collection

### Build and Run

```bash
# Build
docker build -f Dockerfile.prod -t intell-backend .

# Run
docker run -p 8000:8000 \
  -e SECRET_KEY=your-secret-key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  intell-backend
```

### With Docker Compose

Use the production docker-compose from `infrastructure/`:

```bash
cd ../infrastructure
docker-compose -f docker-compose.prod.yml up backend celery-worker
```

### Environment Variables (Production)

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Django secret key |
| `DEBUG` | No | Must be `False` |
| `ALLOWED_HOSTS` | Yes | Comma-separated hostnames |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `CELERY_BROKER_URL` | Yes | Redis URL for Celery |
| `REDIS_URL` | Yes | Redis URL for Channels |
| `CORS_ALLOWED_ORIGINS` | Yes | Frontend URL(s) |

## License

Proprietary - All rights reserved

