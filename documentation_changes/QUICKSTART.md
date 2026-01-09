# Quick Start Guide - Development

Quick guide to get the backend running for development and testing.

## Prerequisites Check

- Python 3.8+ installed
- Docker and Docker Compose installed
- Virtual environment activated (recommended)

## Step-by-Step Setup

### 1. Start Infrastructure Services

```bash
cd infrastructure
docker-compose up -d
```

This starts:
- PostgreSQL on `localhost:5432`
- Redis on `localhost:6379`

### 2. Configure Environment

```bash
cd backend
cp env.example .env
```

Edit `.env` and ensure these are set:
```bash
DATABASE_URL=postgresql://intell_user:patents2026$@localhost:5432/intell
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Verify Infrastructure

```bash
python scripts/check_infrastructure.py
```

Should show:
- ✅ PostgreSQL: Connected
- ✅ Redis (Celery): Connected
- ✅ Redis (Channels): Connected

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Start Services

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
```

**Terminal 2 - Celery Worker (Ingestion I/O):**
```bash
celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4
```

**Terminal 3 - Celery Worker (Charts CPU):**
```bash
celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1
```

**Terminal 4 - Celery Worker (AI):**
```bash
celery -A config worker -Q ai -c 2 --prefetch-multiplier=1
```

## Test the Complete Flow

### 1. Create a Job with Excel File

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -F "source_type=espacenet_excel" \
  -F "source_data=@context/Filters_20250522_1212.xlsx" \
  -F 'images=[{"algorithm_key":"top_patent_countries","algorithm_version":"1.0","params":{"top_n":15},"output_format":"both"}]' \
  -F "idempotency_key=test-001"
```

### 2. Check Job Status

```bash
curl http://localhost:8000/api/jobs/1/
```

### 3. Connect to WebSocket (optional)

Use a WebSocket client to connect to:
```
ws://localhost:8000/ws/jobs/1/
```

### 4. Request AI Description

```bash
curl -X POST http://localhost:8000/api/ai/describe/ \
  -H "Content-Type: application/json" \
  -d '{
    "image_task_id": 1,
    "user_context": "Describe this chart",
    "provider_preference": "mock"
  }'
```

## Troubleshooting

### Services Not Starting

```bash
# Check docker-compose services
cd infrastructure
docker-compose ps

# View logs
docker-compose logs -f
```

### Database Connection Issues

```bash
# Verify PostgreSQL is running
docker-compose exec db pg_isready -U intell_user

# Check connection string in .env
# Should be: postgresql://intell_user:patents2026$@localhost:5432/intell
```

### Redis Connection Issues

```bash
# Verify Redis is running
docker-compose exec redis redis-cli ping

# Check Redis URLs in .env
# CELERY_BROKER_URL=redis://localhost:6379/0
# REDIS_URL=redis://localhost:6379/1
```

### Celery Workers Not Processing Tasks

1. Verify workers are connected to correct queues:
   ```bash
   celery -A config inspect active_queues
   ```

2. Check worker logs for errors

3. Verify Redis is accessible from workers

## Next Steps

- Run end-to-end test: `python manage.py test apps.jobs.tests.JobPipelineTestCase`
- Access admin: http://localhost:8000/admin/
- Check API docs: http://localhost:8000/api/

