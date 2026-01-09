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

## Quick Start (Automated Setup)

### From Scratch Setup

**Linux/macOS:**
```bash
cd infrastructure
chmod +x setup.sh
./setup.sh
```

**Windows (PowerShell):**
```powershell
cd infrastructure
.\setup.ps1
```

This script will:
1. Stop any existing containers
2. Start infrastructure services
3. Wait for PostgreSQL and Redis to be ready
4. Verify database setup

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
   # Use automated setup script (recommended)
   ./setup.sh  # Linux/macOS
   # or
   .\setup.ps1  # Windows PowerShell
   
   # Or manually:
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

## Notes

- Django and Celery workers run **locally** for easier development and debugging
- Infrastructure services (PostgreSQL, Redis) run in Docker
- Volumes persist data between container restarts
- Database is automatically created and initialized on first startup
- For production, consider running Django and Celery in Docker as well
