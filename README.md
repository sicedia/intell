# Intelli - Patent Analysis Platform

Monorepo application for patent data analysis and visualization with Django backend (REST API + WebSocket), Next.js frontend (TypeScript), Celery workers, and Redis.

## 📁 Project Structure

```
intell/
├── backend/              # Django REST API + WebSocket (Channels)
│   ├── config/           # Django configuration (settings, celery, asgi)
│   ├── apps/             # Django applications
│   │   ├── algorithms/   # Chart generation algorithms
│   │   ├── jobs/         # Job orchestration (Celery tasks)
│   │   ├── datasets/     # Data normalization
│   │   ├── audit/        # Event logging
│   │   └── ...
│   ├── manage.py
│   └── requirements.txt
├── frontend/             # Next.js Application
│   ├── src/
│   │   ├── app/          # Next.js App Router
│   │   ├── features/     # Feature modules
│   │   └── shared/       # Shared components/utils
│   └── package.json
├── infrastructure/       # Docker Compose configs
│   ├── docker-compose.yml      # Development (DB + Redis only)
│   ├── docker-compose.prod.yml # Production (all services)
│   └── nginx/            # Nginx config for production
└── README.md
```

## 🚀 Quick Start (Development)

### Prerequisites

- **Python 3.11+** (recommended 3.13)
- **Node.js 20+**
- **Docker** and **Docker Compose** (for PostgreSQL and Redis)
- **npm** or **pnpm**

### Step 1: Start Infrastructure Services

```bash
cd infrastructure

# Linux/macOS
./setup.sh

# Windows PowerShell
.\setup.ps1

# Or manually:
docker-compose up -d
```

This starts:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`

### Step 2: Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp env.example .env

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### Step 3: Start Backend Services

You need **3 terminals** for full functionality:

**Terminal 1 - Django Server:**
```bash
cd backend
.venv\Scripts\activate  # or source .venv/bin/activate
python manage.py runserver
```

**Terminal 2 - Celery Worker:**
```bash
cd backend
.venv\Scripts\activate

# Windows (development):
python -m celery -A config worker --loglevel=info --pool=solo

# Linux/macOS (development):
celery -A config worker --loglevel=info
```

**Terminal 3 - (Optional) Multiple Queues:**
```bash
# For separate queue processing:
celery -A config worker -Q charts_cpu --loglevel=info
```

### Step 4: Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp env.example .env.local

# Start development server
npm run dev
```

### Step 5: Verify Everything Works

| Service | URL | Status Check |
|---------|-----|--------------|
| Frontend | http://localhost:3000 | Open in browser |
| Backend API | http://localhost:8000/api/ | Open in browser |
| API Docs | http://localhost:8000/api/docs/ | Swagger UI |
| Health Check | http://localhost:8000/api/health/ | JSON response |
| Admin | http://localhost:8000/admin/ | Django admin |

### Environment Variables

**Backend** (`backend/.env`):
```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://intell_user:patents2026$@localhost:5432/intell
CELERY_BROKER_URL=redis://localhost:6379/0
REDIS_URL=redis://localhost:6379/1
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_BASE_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_ENV=development
```

---

## 🏭 Production Deployment

### Option 1: Docker Compose (Recommended)

All services run in Docker containers with Nginx as reverse proxy.

#### Step 1: Configure Environment

```bash
cd infrastructure

# Copy environment templates
cp env.example .env
cp backend.env.example backend.env

# Edit with production values
nano .env          # Database credentials, frontend URLs
nano backend.env   # Django secret key, allowed hosts, etc.
```

**Important variables in `backend.env`:**
```env
SECRET_KEY=your-super-secret-production-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True
```

#### Step 2: Configure SSL (Optional but Recommended)

```bash
mkdir -p nginx/ssl
# Copy your certificates:
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# Uncomment HTTPS block in nginx/nginx.conf
```

#### Step 3: Build and Deploy

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create admin user
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

#### Step 4: Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl http://localhost/api/health/
```

### Production Architecture

```
                    ┌─────────────┐
                    │   Nginx     │ :80/:443
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  Frontend   │ │   Backend   │ │   Static    │
    │  (Next.js)  │ │  (Django +  │ │   Files     │
    │   :3000     │ │   Daphne)   │ │  /static/   │
    └─────────────┘ │   :8000     │ │  /media/    │
                    └──────┬──────┘ └─────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Celery    │ │    Redis    │ │ PostgreSQL  │
    │   Worker    │ │   :6379     │ │   :5432     │
    │  (prefork)  │ └─────────────┘ └─────────────┘
    └─────────────┘
```

### Scaling

```bash
# Scale Celery workers for high load
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4
```

### Backup & Restore

```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U intell_user intell > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U intell_user intell < backup.sql
```

---

## 🔧 Configuration

### Backend Configuration

Configuration files in `backend/config/settings/`:

| File | Purpose |
|------|---------|
| `base.py` | Shared settings (installed apps, middleware) |
| `development.py` | Development settings (DEBUG=True, SQLite option) |
| `production.py` | Production settings (security, PostgreSQL) |

### Celery Configuration

Celery is configured in `backend/config/celery.py`:

- **Windows**: Uses `solo` pool (sequential, for development)
- **Linux/macOS**: Uses `prefork` pool (parallel, for production)

Task queues:
- `ingestion_io` - Data ingestion tasks
- `charts_cpu` - Chart generation (CPU intensive)
- `ai` - AI description generation

### Frontend Configuration

Environment variables are validated with Zod in `frontend/src/shared/lib/env.ts`

## 🛠️ Technologies Used

### Backend
- **Django 5.x** - Python web framework
- **Django REST Framework** - REST API
- **Django Channels** - WebSocket support
- **Daphne** - ASGI server
- **Celery** - Async task queue
- **Redis** - Message broker + cache
- **PostgreSQL** - Database (production)

### Frontend
- **Next.js 16** - React framework
- **React 19** - UI library
- **TypeScript 5** - Static typing
- **Tailwind CSS 4** - Styling
- **@tanstack/react-query** - Server state
- **Zustand** - Client state
- **Sonner** - Toast notifications

### Infrastructure
- **Docker** - Containerization
- **Nginx** - Reverse proxy (production)
- **Docker Compose** - Orchestration

## 📝 Useful Commands

### Infrastructure

```bash
# Start PostgreSQL and Redis
cd infrastructure && docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (reset data)
docker-compose down -v

# View logs
docker-compose logs -f redis db
```

### Backend

```bash
cd backend

# Django
python manage.py runserver          # Start server
python manage.py migrate            # Apply migrations
python manage.py makemigrations     # Create migrations
python manage.py createsuperuser    # Create admin user
python manage.py collectstatic      # Collect static files

# Celery (Development)
# Windows:
python -m celery -A config worker --loglevel=info --pool=solo

# Linux/macOS:
celery -A config worker --loglevel=info

# Multiple queues:
celery -A config worker -Q charts_cpu,ingestion_io --loglevel=info

# Tests
pytest                              # Run all tests
pytest apps/jobs/tests/             # Run specific tests
```

### Frontend

```bash
cd frontend

npm run dev          # Development server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test         # Run tests
```

### Docker (Production)

```bash
cd infrastructure

# Build and start all services
docker-compose -f docker-compose.prod.yml up -d --build

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Execute commands in containers
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4

# Stop all
docker-compose -f docker-compose.prod.yml down
```

## 🧪 Development

### Recommended Workflow

**Terminal Setup (4 terminals recommended):**

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `cd infrastructure && docker-compose up` | PostgreSQL + Redis |
| 2 | `cd backend && python manage.py runserver` | Django API |
| 3 | `cd backend && celery -A config worker --pool=solo -l info` | Celery worker |
| 4 | `cd frontend && npm run dev` | Next.js frontend |

### API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/jobs/` | Create new job (upload Excel, select algorithms) |
| `GET /api/jobs/{id}/` | Get job details with all image tasks |
| `POST /api/jobs/{id}/cancel/` | Cancel a running job |
| `POST /api/image-tasks/{id}/retry/` | Retry a failed image task |
| `POST /api/image-tasks/{id}/cancel/` | Cancel an image task |
| `GET /api/health/` | Health check endpoint |
| `GET /api/docs/` | Swagger API documentation |

### WebSocket

Real-time job progress updates via WebSocket:

```
ws://localhost:8000/ws/jobs/{job_id}/
```

Events: `START`, `PROGRESS`, `DONE`, `ERROR`, `CANCELLED`, `RETRY`

### Project Structure

**Backend Apps:**
- `apps/jobs/` - Job orchestration, ImageTask model, Celery tasks
- `apps/algorithms/` - Chart generation algorithms (patent trends, etc.)
- `apps/datasets/` - Data normalization from Excel/API
- `apps/audit/` - Event logging for WebSocket

**Frontend Features:**
- `features/generation/` - Job creation wizard, progress tracking
- `shared/lib/api-client.ts` - API client with error handling
- `shared/store/connection-store.ts` - Connection state management

## 🔍 Troubleshooting

### Redis Connection Error

```bash
# Check if Redis is running
docker-compose -f infrastructure/docker-compose.yml ps

# Restart Redis
docker-compose -f infrastructure/docker-compose.yml restart redis
```

### Celery Tasks Not Running

```bash
# Check Celery worker is running
# Windows must use --pool=solo

# Check Redis connection
redis-cli ping  # Should return PONG
```

### WebSocket Not Connecting

1. Ensure Django is running with Daphne (ASGI)
2. Check `CHANNEL_LAYERS` configuration in settings
3. Verify Redis is running on port 6379

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose -f infrastructure/docker-compose.yml exec db pg_isready -U intell_user -d intell

# Reset database (WARNING: destroys data)
docker-compose -f infrastructure/docker-compose.yml down -v
docker-compose -f infrastructure/docker-compose.yml up -d
```

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [Django Channels](https://channels.readthedocs.io/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [Next.js Documentation](https://nextjs.org/docs)
- [React Query](https://tanstack.com/query/latest)

## 🔒 Security Notes

- **SECRET_KEY**: Generate a new one for production
- **DEBUG**: Must be `False` in production
- **ALLOWED_HOSTS**: Configure your domain(s)
- **CORS_ALLOWED_ORIGINS**: Only allow your frontend domain
- **SSL**: Enable HTTPS in production (`SECURE_SSL_REDIRECT=True`)

## 📄 License

Proprietary - All rights reserved

