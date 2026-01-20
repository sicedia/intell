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
- **Initialization**: Automatically creates database and sets up permissions via `init-db.sql`

### Redis
- **Image**: redis:7
- **Port**: 6379
- **Usage**:
  - DB 0: Celery broker and result backend
  - DB 1: Django Channels (WebSocket)
- **Volume**: redis_data (persistent with AOF)

## Quick Start

### Manual Start

If you prefer to start services manually:

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
# PostgreSQL (specify database name to avoid connection errors)
docker-compose exec db pg_isready -U intell_user -d intell

# Redis
docker-compose exec redis redis-cli ping
```

## Development Setup

For development, run Django and Celery workers **locally** (not in Docker):

### Complete Setup (Recommended)

1. **Start infrastructure services:**
   ```bash
   cd infrastructure
   docker-compose up -d
   ```

2. **Configure environment variables** in `backend/.env`:
   ```bash
   cd ../backend
   cp env.example .env
   # Edit .env with your settings (DATABASE_URL is already configured)
   ```

3. **Run automated backend setup:**
   ```bash
   python scripts/setup_dev.py
   ```
   
   This will:
   - Check infrastructure connectivity
   - Wait for database to be ready
   - Run Django migrations
   - Create a superuser (optional)

4. **Start Django server** (in `backend/` directory):
   ```bash
   python manage.py runserver
   ```

5. **Run Celery workers** (in separate terminals, in `backend/` directory):
   ```bash
   # Terminal 1 - Ingestion I/O
   celery -A config worker -Q ingestion_io -c 4 --prefetch-multiplier=4
   
   # Terminal 2 - Charts CPU
   celery -A config worker -Q charts_cpu -c 2 --prefetch-multiplier=1
   
   # Terminal 3 - AI
   celery -A config worker -Q ai -c 2 --prefetch-multiplier=1
   ```

### Manual Setup (Alternative)

If you prefer to set up manually:

1. Start infrastructure: `cd infrastructure && docker-compose up -d`
2. Configure `.env`: `cd ../backend && cp env.example .env`
3. Run migrations: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`

## Environment Variables

Create a `.env` file in the `infrastructure/` directory (optional) or use defaults:

```bash
POSTGRES_DB=intell
POSTGRES_USER=intell_user
POSTGRES_PASSWORD=patents2026$
```

## Database Initialization

The database is automatically initialized when the PostgreSQL container starts for the first time:

- The database `intell` is created automatically by PostgreSQL (via `POSTGRES_DB`)
- The initialization script `init-db.sql` sets up proper permissions
- The script runs only on first startup (when the data volume is empty)
- To reinitialize, remove the volume: `docker-compose down -v`

## Troubleshooting

### Database "intell_user" does not exist error

This error occurs when something tries to connect using the username as the database name. The fix:

1. **Healthcheck fix**: The healthcheck now specifies the database name: `pg_isready -U intell_user -d intell`
2. **Connection string**: Always use the full connection string: `postgresql://intell_user:password@localhost:5432/intell`
3. **Reinitialize**: If the error persists, reset the database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Database not ready

If migrations fail because the database isn't ready:

1. Wait a few seconds after starting containers
2. Check database status: `docker-compose exec db pg_isready -U intell_user -d intell`
3. Use the automated setup script which waits for the database: `python scripts/setup_dev.py`

## Production Deployment

**📘 For complete production deployment guide, see [b-DEPLOYMENT.md](../documentation/b-DEPLOYMENT.md)**

This directory contains the following deployment scripts:

- **`deploy.sh`** - Automated initial deployment script
- **`setup-ssl.sh`** - SSL certificate configuration (Let's Encrypt or custom)
- **`backup-db.sh`** - Database backup script
- **`restore-db.sh`** - Database restore script
- **`update.sh`** - Update script for code updates (git pull + rebuild)
- **`build-and-push.sh`** / **`build-and-push.ps1`** - Build and push Docker images to Docker Hub

### Quick Production Start

1. **Copy and configure environment files:**
   ```bash
   cp .docker.env.example .docker.env
   cp .django.env.example .django.env
   # Edit both files with your production values
   ```

2. **Configure SSL certificates:**
   ```bash
   # Option 1: Use automated script
   chmod +x setup-ssl.sh
   ./setup-ssl.sh
   
   # Option 2: Manually copy certificates
   mkdir -p nginx/ssl
   cp /path/to/fullchain.pem nginx/ssl/
   cp /path/to/privkey.pem nginx/ssl/
   ```

3. **Deploy:**
   ```bash
   # Option 1: Use automated script (recommended)
   chmod +x deploy.sh
   ./deploy.sh
   
   # Option 2: Manual deployment
   docker compose -f docker-compose.prod.yml --env-file .docker.env pull
   docker compose -f docker-compose.prod.yml --env-file .docker.env up -d
   docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput
   docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput
   ```

### Production Services

| Service | Description | Port |
|---------|-------------|------|
| `db` | PostgreSQL 16 | Internal only |
| `redis` | Redis 7 (Celery + Channels) | Internal only |
| `backend` | Django + Daphne (ASGI) | Internal only |
| `celery-worker` | Celery with prefork pool | N/A |
| `frontend` | Next.js (standalone) | Internal only |
| `nginx` | Reverse proxy | 80, 443 |

### Scaling Celery Workers

For high load, scale Celery workers:

```bash
docker-compose -f docker-compose.prod.yml --env-file .docker.env up -d --scale celery-worker=4
```

### Monitoring

```bash
# View all logs
docker-compose -f docker-compose.prod.yml --env-file .docker.env logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml --env-file .docker.env logs -f backend celery-worker

# Check service status
docker-compose -f docker-compose.prod.yml --env-file .docker.env ps
```

### Backup Database

```bash
# Use automated script (recommended)
./backup-db.sh

# Or manually
docker-compose -f docker-compose.prod.yml --env-file .docker.env exec db pg_dump -U intell_user intell > backup.sql
```

### Restore Database

```bash
# Use automated script (recommended)
./restore-db.sh backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz

# Or manually
docker-compose -f docker-compose.prod.yml --env-file .docker.env exec -T db psql -U intell_user intell < backup.sql
```

## Available Scripts

For complete information about deployment scripts, see [c-DEPLOYMENT_SCRIPTS.md](../documentation/c-DEPLOYMENT_SCRIPTS.md).

## Notes

- Django and Celery workers run **locally** for easier development and debugging
- Infrastructure services (PostgreSQL, Redis) run in Docker
- Volumes persist data between container restarts
- Database is automatically created and initialized on first startup
- For production, use `docker-compose.prod.yml` which includes all services
- **Always use `--env-file .docker.env`** when running docker-compose commands in production