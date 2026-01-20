# Environment Variables Configuration - Intelli

This guide explains how to configure environment variables for development and production.

## .env File Structure

### Backend (Django)

```
backend/
├── env.example              # General example (reference)
├── env.development.example  # For local development
├── env.production.example   # For production
└── .env                     # Your actual file (DO NOT commit)
```

**For development:**
```bash
cd backend
cp env.development.example .env
# Edit .env with your values
```

**For production:**
```bash
cd backend
cp env.production.example .env
# Edit .env with production values
```

### Frontend (Next.js)

```
frontend/
├── env.example              # General example (reference)
├── env.development.example  # For local development
├── env.production.example   # For production (reference)
└── .env.local               # Your actual file for development (DO NOT commit)
```

**For development:**
```bash
cd frontend
cp env.development.example .env.local
# Edit .env.local with your values
```

**For production:**
Production variables are configured in `infrastructure/.env` and passed to the Docker container during build.

### Infrastructure (Docker Compose)

```
infrastructure/
├── .docker.env.example      # Variables for Docker Compose
├── .django.env.example      # Variables for Django in Docker
├── .docker.env              # Your actual file (DO NOT commit)
└── .django.env              # Your actual file (DO NOT commit)
```

**For production:**
```bash
cd infrastructure
cp .docker.env.example .docker.env
cp .django.env.example .django.env
# Edit both files with production values
```

## Structure Explanation

### Why two files in infrastructure?

1. **`infrastructure/.docker.env`** - Variables for Docker Compose:
   - `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` - PostgreSQL configuration
   - `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_WS_BASE_URL` - URLs for frontend build
   - `REDIS_PASSWORD` (optional) - Redis password

2. **`infrastructure/.django.env`** - Variables for Django backend in Docker:
   - `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` - Django configuration
   - `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` - Security
   - `MICROSOFT_CLIENT_ID`, etc. - OAuth
   - Email, logging variables, etc.

**Reason:** Docker Compose needs variables to build services, while Django needs its own configuration variables. Separating them makes configuration clearer and more maintainable.

## Important Variables

### Backend - Development

| Variable | Development Value | Description |
|----------|------------------|-------------|
| `DEBUG` | `True` | Enables debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed hosts |
| `DATABASE_URL` | `postgresql://...@localhost:5432/intell` | Local database |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Frontend origin |

### Backend - Production

| Variable | Production Value | Description |
|----------|------------------|-------------|
| `DEBUG` | `False` | **CRITICAL:** Always False in production |
| `ALLOWED_HOSTS` | `intell.cedia.org.ec` | Your domain |
| `SECRET_KEY` | `[generate new]` | Unique and strong secret key |
| `SECURE_SSL_REDIRECT` | `True` | Redirect HTTP to HTTPS |
| `CORS_ALLOWED_ORIGINS` | `https://intell.cedia.org.ec` | Frontend origin |

### Frontend - Development

| Variable | Development Value | Description |
|----------|------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000/api` | Local backend API |
| `NEXT_PUBLIC_WS_BASE_URL` | `ws://localhost:8000/ws` | Local WebSocket |
| `NEXT_PUBLIC_APP_ENV` | `development` | App environment |

### Frontend - Production

| Variable | Production Value | Description |
|----------|------------------|-------------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://intell.cedia.org.ec/api` | API in production |
| `NEXT_PUBLIC_WS_BASE_URL` | `wss://intell.cedia.org.ec/ws` | Secure WebSocket |
| `NEXT_PUBLIC_APP_ENV` | `production` | App environment |

### Infrastructure - Docker Compose

| Variable | Description |
|----------|-------------|
| `POSTGRES_DB` | Database name |
| `POSTGRES_USER` | PostgreSQL user |
| `POSTGRES_PASSWORD` | **IMPORTANT:** Strong password |
| `NEXT_PUBLIC_API_BASE_URL` | API URL for frontend build |
| `NEXT_PUBLIC_WS_BASE_URL` | WebSocket URL for frontend build |

## Generate SECRET_KEY

For production, generate a new SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Configuration Checklist

### Local Development

- [ ] Copy `backend/env.development.example` to `backend/.env`
- [ ] Copy `frontend/env.development.example` to `frontend/.env.local`
- [ ] Configure `DATABASE_URL` if using PostgreSQL
- [ ] Configure Microsoft OAuth if using it
- [ ] Verify that `DEBUG=True` in backend

### Production

- [ ] Copy `infrastructure/.docker.env.example` to `infrastructure/.docker.env`
- [ ] Copy `infrastructure/.django.env.example` to `infrastructure/.django.env`
- [ ] Generate new `SECRET_KEY` for backend
- [ ] Configure strong password for PostgreSQL
- [ ] Verify that `DEBUG=False` in backend
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Configure `CORS_ALLOWED_ORIGINS` with your domain
- [ ] Enable all SSL security configurations
- [ ] Configure Microsoft OAuth with production URLs
- [ ] Configure SMTP email if necessary

## Security

⚠️ **NEVER**:
- Commit `.env`, `.env.local`, `.docker.env`, `.django.env` files to the repository
- Share secrets in plain text
- Use the same `SECRET_KEY` in development and production
- Leave `DEBUG=True` in production

✅ **ALWAYS**:
- Use strong and unique passwords
- Generate new `SECRET_KEY` for each environment
- Review `.env.example` files before creating the actual ones
- Keep `.env` files out of version control

## Troubleshooting

### Backend not reading environment variables

1. Verify that the file is named `.env` (not `env`)
2. Verify that it's in the `backend/` directory
3. Restart the Django server

### Frontend not reading environment variables

1. Verify that the file is named `.env.local` (not `.env`)
2. Verify that it's in the `frontend/` directory
3. Variables must start with `NEXT_PUBLIC_`
4. Restart the Next.js server

### Variables not passed in Docker

1. Verify that `infrastructure/.docker.env` exists
2. Verify that `infrastructure/.django.env` exists
3. Verify syntax in `docker-compose.prod.yml`
4. Rebuild containers: `docker-compose build --no-cache`
