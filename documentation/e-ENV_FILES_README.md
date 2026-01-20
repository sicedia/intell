# Environment Variable Files - Infrastructure

## File Structure

```
infrastructure/
├── .docker.env.example    # Variables for Docker Compose (example)
├── .django.env.example    # Variables for Django backend (example)
├── .docker.env            # Your actual Docker file (DO NOT commit)
└── .django.env            # Your actual Django file (DO NOT commit)
```

## File Description

### `.docker.env.example` / `.docker.env`

**Purpose:** Environment variables for Docker Compose used to configure infrastructure services.

**Contains:**
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - PostgreSQL user
- `POSTGRES_PASSWORD` - PostgreSQL password (change in production!)
- `REDIS_PASSWORD` - Redis password (optional)
- `NEXT_PUBLIC_API_BASE_URL` - API URL for frontend build
- `NEXT_PUBLIC_WS_BASE_URL` - WebSocket URL for frontend build

**Usage:**
```bash
cp .docker.env.example .docker.env
# Edit .docker.env with your values
```

### `.django.env.example` / `.django.env`

**Purpose:** Environment variables specific to the Django backend service in Docker.

**Contains:**
- `SECRET_KEY` - Django secret key (generate new for production!)
- `DEBUG` - Debug mode (False in production)
- `ALLOWED_HOSTS` - Allowed hosts
- `CORS_ALLOWED_ORIGINS` - Allowed origins for CORS
- `CSRF_TRUSTED_ORIGINS` - Trusted origins for CSRF
- SSL security configuration
- Microsoft OAuth configuration
- Email configuration
- Logging configuration

**Usage:**
```bash
cp .django.env.example .django.env
# Edit .django.env with your values
```

## Why Two Separate Files?

1. **`.docker.env`** - Used by Docker Compose to:
   - Configure infrastructure services (PostgreSQL, Redis)
   - Pass variables to frontend build
   - Variables shared between services

2. **`.django.env`** - Used specifically by the Django container:
   - Django security configuration
   - Application-specific secrets
   - Variables that should not be in the Docker Compose file

**Advantages:**
- Clear separation of responsibilities
- Better organization and maintainability
- Facilitates secret management
- Allows different access levels

## Initial Configuration

### For Production

```bash
cd infrastructure

# Copy example files
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Edit with your values
nano .docker.env
nano .django.env
```

### Critical Variables

**In `.docker.env`:**
- `POSTGRES_PASSWORD` - **IMPORTANT:** Use a strong password
- `NEXT_PUBLIC_API_BASE_URL` - Your API URL in production
- `NEXT_PUBLIC_WS_BASE_URL` - Your WebSocket URL in production

**In `.django.env`:**
- `SECRET_KEY` - **CRITICAL:** Generate a new unique key
- `DEBUG` - **CRITICAL:** Must be `False` in production
- `ALLOWED_HOSTS` - Your production domain
- `CORS_ALLOWED_ORIGINS` - Your production domain with https://

## Generate SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Security

⚠️ **NEVER:**
- Commit `.docker.env` or `.django.env` to the repository
- Share these files in plain text
- Use the same values in development and production

✅ **ALWAYS:**
- Use strong and unique passwords
- Generate new `SECRET_KEY` for production
- Verify that `DEBUG=False` in production
- Keep these files out of version control

## Code References

- `docker-compose.prod.yml` - Uses `.django.env` for the backend service
- `deploy.sh` - Verifies and creates these files if they don't exist
- `backup-db.sh` - Reads `.docker.env` for PostgreSQL credentials
- `restore-db.sh` - Reads `.docker.env` for PostgreSQL credentials
