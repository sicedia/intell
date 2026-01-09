# Intelli Backend

Django + DRF + Celery + Redis + Channels + PostgreSQL + LangChain backend for patent data processing and chart generation.

## Architecture

The backend follows a canonical Dataset pipeline:
```
ingestion (raw) → normalize() → persist Dataset → Job FK→Dataset → ImageTask consume Dataset → algorithm recibe Dataset
```

All algorithms consume `datasets.Dataset` (never raw data). EventLog is append-only with `emit_event()` as the single source of truth.

## Project Structure

```
backend/
├── apps/
│   ├── core/              # Shared utilities and exceptions
│   ├── ingestion/         # Data source connectors
│   ├── datasets/          # Canonical dataset normalization
│   ├── algorithms/        # Chart generation algorithms
│   ├── jobs/              # Job orchestration and API
│   ├── artifacts/         # Artifact storage
│   ├── ai_descriptions/   # AI-powered chart descriptions
│   └── audit/             # Append-only event logging
├── config/                # Django configuration
├── context/               # Test data and examples
└── media/                 # Media files (datasets, artifacts)
```

## Setup

### Prerequisites

- Python 3.8+
- Docker and Docker Compose (for infrastructure services)
- PostgreSQL (via docker-compose)
- Redis (via docker-compose)

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
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # The DATABASE_URL is already configured in env.example
   ```

4. **Run automated backend setup:**
   ```bash
   python scripts/setup_dev.py
   ```
   
   This script will:
   - Check if infrastructure services are running
   - Wait for database to be ready
   - Run Django migrations automatically
   - Create a superuser interactively (optional)
   
   Options:
   ```bash
   python scripts/setup_dev.py --skip-superuser  # Skip superuser creation
   python scripts/setup_dev.py --skip-infrastructure-check  # Skip infrastructure check
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
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
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
   python scripts/check_infrastructure.py
   ```

5. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser:**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

### Django Server

```bash
python manage.py runserver
```

Server runs at `http://localhost:8000`

### Celery Workers

Run 3 separate workers for different queues:

**Terminal 1 - Ingestion I/O queue:**
```bash
celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4
```

**Terminal 2 - Charts CPU queue:**
```bash
celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1
```

**Terminal 3 - AI queue:**
```bash
celery -A config worker -Q ai -c 2 --prefetch-multiplier=1
```

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
python scripts/check_infrastructure.py
```

## API Endpoints

### Health Checks

- `GET /api/health/` - Basic health check
- `GET /api/health/redis/` - Redis health check
- `GET /api/health/celery/` - Celery health check

### Jobs

- `POST /api/jobs/` - Create a new job
- `GET /api/jobs/<id>/` - Get job details
- `POST /api/jobs/<id>/cancel/` - Cancel a job

### Tasks

- `GET /api/image-tasks/<id>/` - Get image task details
- `GET /api/description-tasks/<id>/` - Get description task details

### AI Descriptions

- `POST /api/ai/describe/` - Create AI description task

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

Event payload structure:
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

## Testing

The project uses **pytest** and **pytest-django** for testing. Tests are organized by app in `apps/*/tests/` and integration tests in `backend/tests/`.

### Running Tests

**Run all tests:**
```bash
pytest
```

**Run tests with migrations (required for integration tests):**
```bash
pytest --migrations
```

**Run specific test file:**
```bash
pytest apps/algorithms/tests/test_registry.py
```

**Run specific test:**
```bash
pytest apps/audit/tests/test_emit_event.py::TestEmitEvent::test_emit_event_for_job
```

**Run with coverage:**
```bash
pytest --cov=apps --cov-report=html
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

`finalize_job` calculates final status:
- **SUCCESS**: All ImageTasks succeed
- **PARTIAL_SUCCESS**: Some succeed, some fail
- **FAILED**: All fail
- `progress_total` = average of ImageTask progress values

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

## License

[Your License Here]

