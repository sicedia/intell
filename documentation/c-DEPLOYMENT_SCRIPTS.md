# Deployment Scripts - Infrastructure

This document describes the scripts available in the `infrastructure/` directory for deploying and maintaining the application in production.

## Available Scripts

### 1. `deploy.sh` - Automated Initial Deployment

**Purpose:** Main script for the initial deployment of the application in production.

**Usage:**
```bash
cd /opt/intell/infrastructure
chmod +x deploy.sh
./deploy.sh
```

**What it does:**
1. Verifies that Docker and Docker Compose are installed
2. Verifies that `.docker.env` and `.django.env` exist
3. Verifies SSL certificates (optional)
4. Builds and starts all services
5. Waits for services to be healthy
6. Runs database migrations
7. Collects static files
8. Creates superuser if it doesn't exist

**Requirements:**
- Docker and Docker Compose installed
- `.docker.env` and `.django.env` files configured
- SSL certificates in `nginx/ssl/` (optional, but recommended)

---

### 2. `setup-ssl.sh` - SSL Certificate Configuration

**Purpose:** Interactive script to configure SSL certificates (Let's Encrypt or custom certificates).

**Usage:**
```bash
cd /opt/intell/infrastructure
chmod +x setup-ssl.sh
./setup-ssl.sh
```

**Options:**
- **Option 1:** Let's Encrypt (automatic) - Requires DNS to be configured correctly
- **Option 2:** Custom certificate - Allows specifying paths to existing certificates
- **Option 3:** Skip SSL configuration

**What it does:**
- Installs Certbot if necessary (for Let's Encrypt)
- Generates or copies certificates to `nginx/ssl/`
- Sets correct permissions
- Configures automatic renewal (for Let's Encrypt)
- Validates nginx configuration

---

### 3. `backup-db.sh` - Database Backup

**Purpose:** Creates timestamped backups of the PostgreSQL database.

**Usage:**
```bash
cd /opt/intell/infrastructure
chmod +x backup-db.sh

# Simple backup
./backup-db.sh

# Backup with automatic cleanup of old backups (>30 days)
./backup-db.sh --cleanup
```

**What it does:**
1. Reads credentials from `.docker.env`
2. Creates `backups/` directory if it doesn't exist
3. Generates timestamped backup: `intell_backup_YYYYMMDD_HHMMSS.sql.gz`
4. Lists recent backups
5. Optionally cleans up old backups (>30 days)

**Backup location:**
- `infrastructure/backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz`

**Recommendation:**
- Run daily via cron:
```bash
# Add to crontab: crontab -e
0 2 * * * cd /opt/intell/infrastructure && ./backup-db.sh --cleanup
```

---

### 4. `restore-db.sh` - Restore Database

**Purpose:** Restores the database from a backup file.

**Usage:**
```bash
cd /opt/intell/infrastructure
chmod +x restore-db.sh

# List available backups
ls -lh backups/

# Restore from backup
./restore-db.sh backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz
```

**What it does:**
1. Verifies that the backup file exists
2. Reads credentials from `.docker.env`
3. Stops services that use the database (optional)
4. Restores backup (supports `.sql` and `.sql.gz`)
5. Restarts services

**⚠️ Warning:**
- This script **REPLACES** the current database
- Make a backup before restoring
- Services may be inactive during restoration

---

### 5. `update.sh` - Update Code in Production

**Purpose:** Updates code from git, rebuilds containers, and restarts services.

**Usage:**
```bash
cd /opt/intell/infrastructure
chmod +x update.sh
./update.sh
```

**What it does:**
1. Runs `git pull` (if it's a git repository)
2. Creates automatic database backup
3. Stops services
4. Rebuilds Docker images (`--no-cache`)
5. Starts services
6. Runs migrations
7. Collects static files

**⚠️ Note:**
- This script **rebuilds images** on the server (consumes resources and time)
- **Recommended method:** Use `build-and-push.sh` to build images locally and then `docker compose pull` on the server

---

### 6. `build-and-push.sh` / `build-and-push.ps1` - Build and Push Docker Images

**Purpose:** Builds Docker images (backend and frontend) and pushes them to Docker Hub.

**Usage:**
```bash
# Linux/macOS
cd infrastructure
chmod +x build-and-push.sh
./build-and-push.sh v1.0.1

# Windows PowerShell
cd infrastructure
.\build-and-push.ps1 v1.0.1
```

**What it does:**
1. Reads configuration from `.build.env`
2. Builds backend image: `sicedia/intell-backend:VERSION`
3. Builds frontend image: `sicedia/intell-frontend:VERSION`
4. Tags both images with `latest` as well
5. Pushes them to Docker Hub

**Requirements:**
- Logged into Docker Hub: `docker login`
- `.build.env` file configured with `PRODUCTION_DOMAIN` or API/WS URLs

**Recommended workflow:**
```bash
# 1. In development: build and push
./build-and-push.sh v1.0.2

# 2. On server: update .docker.env with IMAGE_TAG=v1.0.2
# 3. On server: docker compose pull && docker compose up -d
```

---

## Unavailable / Removed Scripts

The following scripts **DO NOT EXIST** and should not be referenced in documentation:

- ❌ `setup.sh` - Does not exist (use `docker-compose up -d` manually)
- ❌ `setup.ps1` - Does not exist (use `docker-compose up -d` manually)

---

## Recommended Execution Order (First Time)

```bash
cd /opt/intell/infrastructure

# 1. Configure environment variables
cp .docker.env.example .docker.env
cp .django.env.example .django.env
nano .docker.env  # Edit values
nano .django.env  # Edit values

# 2. Configure SSL
chmod +x setup-ssl.sh
./setup-ssl.sh

# 3. Deploy
chmod +x deploy.sh
./deploy.sh
```

---

## Execution Order for Updates

**Recommended Method (with pre-built Docker images):**

```bash
# In development: build and push
cd infrastructure
./build-and-push.sh v1.0.2

# On server: update
cd /opt/intell/infrastructure
nano .docker.env  # Change IMAGE_TAG=v1.0.2
docker compose -f docker-compose.prod.yml --env-file .docker.env pull
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput
```

**Alternative Method (build on server):**

```bash
cd /opt/intell/infrastructure
./update.sh
```

---

## Required Permissions

All scripts must be executable:

```bash
chmod +x deploy.sh setup-ssl.sh backup-db.sh restore-db.sh update.sh build-and-push.sh
```

---

## Required Environment Variables

The scripts read the following environment variables:

- **`.docker.env`**: Used by `docker-compose.prod.yml`, `backup-db.sh`, `restore-db.sh`
- **`.django.env`**: Used by the backend container (Django)
- **`.build.env`**: Used by `build-and-push.sh` to build frontend with correct URLs

See [e-ENV_FILES_README.md](e-ENV_FILES_README.md) for more details about environment variables.

---

## Troubleshooting

### Script won't execute

```bash
# Verify permissions
ls -la deploy.sh

# Make executable
chmod +x deploy.sh
```

### Environment variable error

```bash
# Verify that files exist
ls -la .docker.env .django.env

# Verify syntax
cat .docker.env | grep -v '^#' | grep -v '^$'
```

### Docker Compose error

```bash
# Use --env-file explicitly
docker compose -f docker-compose.prod.yml --env-file .docker.env config
```

---

For more information about production deployment, see [b-DEPLOYMENT.md](b-DEPLOYMENT.md).
