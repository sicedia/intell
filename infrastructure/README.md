# Infrastructure - Docker Compose

Docker Compose configuration for Intelli project infrastructure services.

## Services

### PostgreSQL Database
- **Image**: postgres:16
- **Port**: 5432
- **Database**: intell (configurable via POSTGRES_DB)
- **User**: intell_user (configurable via POSTGRES_USER)
- **Password**: patents2026$ (configurable via POSTGRES_PASSWORD)
- **Volume**: postgres_data (persistent)

### Redis
- **Image**: redis:7
- **Port**: 6379
- **Usage**:
  - DB 0: Celery broker and result backend
  - DB 1: Django Channels (WebSocket)
- **Volume**: redis_data (persistent with AOF)

## Usage

### Start Services

```bash
cd infrastructure
docker-compose up -d
```

### Stop Services

```bash
docker-compose down
```

### Stop and Remove Volumes

```bash
docker-compose down -v
```

### View Logs

```bash
docker-compose logs -f
```

### Check Service Health

```bash
# PostgreSQL
docker-compose exec db pg_isready -U intell_user

# Redis
docker-compose exec redis redis-cli ping
```

## Development Setup

For development, run Django and Celery workers **locally** (not in Docker):

1. **Start infrastructure services:**
   ```bash
   cd infrastructure
   docker-compose up -d
   ```

2. **Configure environment variables** in `backend/.env`:
   ```bash
   DATABASE_URL=postgresql://intell_user:patents2026$@localhost:5432/intell
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   REDIS_URL=redis://localhost:6379/1
   ```

3. **Run Django server** (in `backend/` directory):
   ```bash
   python manage.py runserver
   ```

4. **Run Celery workers** (in separate terminals, in `backend/` directory):
   ```bash
   # Terminal 1 - Ingestion I/O
   celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4
   
   # Terminal 2 - Charts CPU
   celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1
   
   # Terminal 3 - AI
   celery -A config worker -Q ai -c 2 --prefetch-multiplier=1
   ```

## Environment Variables

Create a `.env` file in the `infrastructure/` directory (optional) or use defaults:

```bash
POSTGRES_DB=intell
POSTGRES_USER=intell_user
POSTGRES_PASSWORD=patents2026$
```

## Notes

- Django and Celery workers run **locally** for easier development and debugging
- Infrastructure services (PostgreSQL, Redis) run in Docker
- Volumes persist data between container restarts
- For production, consider running Django and Celery in Docker as well
