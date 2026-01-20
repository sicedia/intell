# Production Deployment Guide - Intelli

This guide provides step-by-step instructions for deploying Intelli on an Ubuntu 24.04 LTS server in production.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Initial Configuration](#initial-configuration)
4. [SSL Configuration](#ssl-configuration)
5. [Deployment](#deployment)
6. [Verification](#verification)
7. [Maintenance](#maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Recommended Hardware

- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 50 GB SSD
- **Network**: Stable connection with ports 80 and 443 open

### Required Software

- **Operating System**: Ubuntu 24.04 LTS
- **Docker**: Version 24.0 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: To clone the repository

### Domain and DNS

- Configured domain: `intell.cedia.org.ec`
- DNS A/AAAA records pointing to the server
- SSL certificate (wildcard `*.cedia.edu.ec` or specific)

---

## Server Preparation

### 1. Update the System

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y curl wget git ufw
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group (replace 'user' with your username)
sudo usermod -aG docker $USER

# Install Docker Compose Plugin
sudo apt install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

**Note**: Log out and log back in for group changes to take effect.

### 3. Configure Firewall (UFW)

```bash
# Enable UFW
sudo ufw enable

# Allow SSH (IMPORTANT: do this before blocking everything)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Verify status
sudo ufw status
```

### 4. Clone the Repository

```bash
# Create directory for the application
sudo mkdir -p /opt/intell
sudo chown $USER:$USER /opt/intell

# Clone repository (replace with your URL)
cd /opt/intell
git clone <your-repository-url> .

# Or if you already have the code, copy it to the server
```

---

## Initial Configuration

### 1. Configure Environment Variables

```bash
cd /opt/intell/infrastructure

# Copy example files
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Edit with your values
nano .docker.env
nano .django.env
```

**Minimum configuration in `.docker.env`**:

```env
POSTGRES_DB=intell
POSTGRES_USER=intell_user
POSTGRES_PASSWORD=<strong-generated-password>
NEXT_PUBLIC_API_BASE_URL=https://intell.cedia.org.ec/api
NEXT_PUBLIC_WS_BASE_URL=wss://intell.cedia.org.ec/ws
```

**Minimum configuration in `.django.env`**:

```env
SECRET_KEY=<generate-new-secret-key>
DEBUG=False
ALLOWED_HOSTS=intell.cedia.org.ec
CORS_ALLOWED_ORIGINS=https://intell.cedia.org.ec
CSRF_TRUSTED_ORIGINS=https://intell.cedia.org.ec
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
# CSRF_COOKIE_HTTPONLY=False is required to allow JavaScript to read the CSRF token
# This is already configured in production.py settings
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

**Generate SECRET_KEY**:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2. Configure Microsoft OAuth (if applicable)

If you use Microsoft authentication, update in `.django.env`:

```env
MICROSOFT_CLIENT_ID=<your-client-id>
MICROSOFT_CLIENT_SECRET=<your-client-secret>
MICROSOFT_TENANT_ID=<your-tenant-id>
MICROSOFT_REDIRECT_URI=https://intell.cedia.org.ec/api/auth/microsoft/callback/
MICROSOFT_LOGIN_REDIRECT_URL=https://intell.cedia.org.ec/en/dashboard
MICROSOFT_LOGIN_ERROR_URL=https://intell.cedia.org.ec/en/login
```

**Important**: Configure these same URLs in Azure Portal > App Registrations > Redirect URIs.

---

## SSL Configuration

### Option 1: Existing Wildcard Certificate

If you already have a wildcard certificate `*.cedia.edu.ec`:

```bash
cd /opt/intell/infrastructure

# Create directory for certificates
mkdir -p nginx/ssl

# Copy certificates (adjust paths according to your case)
cp /path/to/your/fullchain.pem nginx/ssl/
cp /path/to/your/privkey.pem nginx/ssl/

# Set correct permissions
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem
```

### Option 2: Let's Encrypt (Automatic)

```bash
cd /opt/intell/infrastructure

# Make script executable
chmod +x setup-ssl.sh

# Run SSL configuration script
./setup-ssl.sh
```

The script will guide you through the process:
1. Select option 1 for Let's Encrypt
2. Make sure DNS points correctly to the server
3. The certificate will be generated automatically

### Option 3: Custom Certificate

```bash
cd /opt/intell/infrastructure

# Run script
./setup-ssl.sh

# Select option 2
# Provide paths to your certificate files
```

---

## Deployment

### Method 1: Deployment with Pre-built Images (Recommended)

This method uses pre-built Docker images uploaded to Docker Hub, avoiding builds on the server.

#### Step 1: Build and Push Images Locally

On your development machine:

```bash
cd infrastructure

# Copy build configuration file
cp .build.env.example .build.env

# Edit .build.env with your production values
nano .build.env
```

**Minimum configuration in `.build.env`**:
```env
NEXT_PUBLIC_API_BASE_URL=https://intell.cedia.org.ec/api
NEXT_PUBLIC_WS_BASE_URL=wss://intell.cedia.org.ec/ws
NEXT_PUBLIC_APP_ENV=production
```

**Build and push images**:

```bash
# Linux/macOS
./build-and-push.sh v1.0.1

# Windows PowerShell
.\build-and-push.ps1 v1.0.1
```

The script:
1. Builds backend and frontend images
2. Tags them with the specified version (e.g., `v1.0.1`) and `latest`
3. Pushes them to Docker Hub (`sicedia/intell-backend` and `sicedia/intell-frontend`)

**Note**: Make sure you are logged into Docker Hub:
```bash
docker login
```

#### Step 2: Configure the Server

On the production server:

```bash
cd /opt/intell/infrastructure

# Copy example files
cp .docker.env.example .docker.env
cp .django.env.example .django.env

# Edit .docker.env
nano .docker.env
```

**Add to `.docker.env`**:
```env
# Docker Image Configuration
IMAGE_TAG=v1.0.1  # or the version you uploaded
```

#### Step 3: Deploy on the Server

```bash
cd /opt/intell/infrastructure

# Make deployment script executable (optional, if you want to use it)
chmod +x deploy.sh

# Option A: Use automated deployment script
./deploy.sh

# Option B: Manual deployment
# Download images from Docker Hub
docker compose -f docker-compose.prod.yml --env-file .docker.env pull

# Start services
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d

# Wait for services to be ready
sleep 15

# Run migrations
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput

# Collect static files
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput

# Create superuser (if it doesn't exist)
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py createsuperuser
```

#### Update to New Version

When you have a new version:

```bash
# 1. In development: build and push new version
./build-and-push.sh v1.0.2

# 2. On server: update .docker.env
# Change IMAGE_TAG=v1.0.2

# 3. On server: download and restart
docker compose -f docker-compose.prod.yml --env-file .docker.env pull
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d

# 4. Run migrations if there are database changes
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput
```

#### Rollback to Previous Version

If you need to go back to a previous version:

```bash
# Change IMAGE_TAG in .docker.env to the previous version
# Example: IMAGE_TAG=v1.0.1

# Download and restart
docker compose -f docker-compose.prod.yml --env-file .docker.env pull
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d
```

### Method 2: Automated Script (Build on Server)

```bash
cd /opt/intell/infrastructure

# Make necessary scripts executable
chmod +x deploy.sh setup-ssl.sh backup-db.sh restore-db.sh

# Run deployment
./deploy.sh
```

The script will:
1. Verify requirements
2. Validate configuration files
3. Build Docker images
4. Start services
5. Run migrations
6. Collect static files
7. Create superuser (if it doesn't exist)

### Method 3: Manual (Build on Server)

**Note**: This method requires building images on the server, which consumes more resources and time.

```bash
cd /opt/intell/infrastructure

# Build images (requires modifying docker-compose.prod.yml to use build:)
docker compose -f docker-compose.prod.yml --env-file .docker.env build

# Start services
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d

# Wait for services to be ready
sleep 15

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate --noinput

# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

---

## Verification

### 1. Verify Service Status

```bash
cd /opt/intell/infrastructure
docker compose -f docker-compose.prod.yml --env-file .docker.env ps
```

All services should show status "Up" and "healthy".

### 2. Verify Logs

```bash
# View all logs
docker compose -f docker-compose.prod.yml --env-file .docker.env logs -f

# View logs of a specific service
docker compose -f docker-compose.prod.yml --env-file .docker.env logs -f backend
docker compose -f docker-compose.prod.yml --env-file .docker.env logs -f frontend
docker compose -f docker-compose.prod.yml --env-file .docker.env logs -f nginx
```

### 3. Test Endpoints

```bash
# Health check
curl https://intell.cedia.org.ec/api/health/

# Verify HTTPS
curl -I https://intell.cedia.org.ec

# Verify HTTP → HTTPS redirect
curl -I http://intell.cedia.org.ec
```

### 4. Verify in Browser

1. Open `https://intell.cedia.org.ec`
2. Verify that the SSL certificate is valid
3. Test login and main functionalities

---

## Maintenance

### Update the Application

**Recommended Method (with pre-built Docker images):**

```bash
cd /opt/intell/infrastructure

# 1. In development: build and push new version
./build-and-push.sh v1.0.2

# 2. On server: update .docker.env with new IMAGE_TAG
nano .docker.env  # Change IMAGE_TAG=v1.0.2

# 3. Download and restart
docker compose -f docker-compose.prod.yml --env-file .docker.env pull
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d

# 4. Run migrations if there are database changes
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput

# 5. Collect static files
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput
```

**Alternative Method (build on server - only if necessary):**

```bash
cd /opt/intell/infrastructure

# Use automated script (updates code from git)
./update.sh

# Or manually:
git pull
docker compose -f docker-compose.prod.yml --env-file .docker.env build --no-cache
docker compose -f docker-compose.prod.yml --env-file .docker.env up -d
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py migrate --noinput
docker compose -f docker-compose.prod.yml --env-file .docker.env exec backend python manage.py collectstatic --noinput
```

### Database Backup

```bash
cd /opt/intell/infrastructure

# Manual backup
./backup-db.sh

# Backup with cleanup of old backups
./backup-db.sh --cleanup

# Backups are saved in: infrastructure/backups/
```

### Restore Database

```bash
cd /opt/intell/infrastructure

# List available backups
ls -lh backups/

# Restore from backup
./restore-db.sh backups/intell_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Restart Services

```bash
cd /opt/intell/infrastructure

# Restart all services
docker compose -f docker-compose.prod.yml restart

# Restart a specific service
docker compose -f docker-compose.prod.yml restart backend
docker compose -f docker-compose.prod.yml restart frontend
docker compose -f docker-compose.prod.yml restart nginx
```

### Stop Services

```bash
cd /opt/intell/infrastructure

# Stop without removing volumes
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (WARNING! Deletes data)
docker compose -f docker-compose.prod.yml down -v
```

### View Resource Usage

```bash
# View container resource usage
docker stats

# View disk usage
docker system df

# Clean unused resources
docker system prune -a
```

### Log Monitoring

```bash
# View logs in real time
docker compose -f docker-compose.prod.yml logs -f

# View last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100

# View logs of a specific service
docker compose -f docker-compose.prod.yml logs -f backend
```

---

## Troubleshooting

### Problem: Services Not Starting

**Solution**:
```bash
# View error logs
docker compose -f docker-compose.prod.yml logs

# Verify configuration
docker compose -f docker-compose.prod.yml config

# Restart Docker
sudo systemctl restart docker
```

### Problem: Database Connection Error

**Solution**:
```bash
# Verify PostgreSQL is running
docker compose -f docker-compose.prod.yml ps db

# Verify PostgreSQL logs
docker compose -f docker-compose.prod.yml logs db

# Verify environment variables
docker compose -f docker-compose.prod.yml exec backend env | grep DATABASE
```

### Problem: 502 Bad Gateway Error

**Solution**:
```bash
# Verify backend is running
docker compose -f docker-compose.prod.yml ps backend

# Verify backend logs
docker compose -f docker-compose.prod.yml logs backend

# Verify nginx logs
docker compose -f docker-compose.prod.yml logs nginx

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problem: SSL Certificate Not Working

**Solution**:
```bash
# Verify certificates exist
ls -lh nginx/ssl/

# Verify permissions
chmod 644 nginx/ssl/fullchain.pem
chmod 600 nginx/ssl/privkey.pem

# Verify nginx configuration
docker compose -f docker-compose.prod.yml exec nginx nginx -t

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problem: Celery Not Processing Tasks

**Solution**:
```bash
# Verify Celery worker is running
docker compose -f docker-compose.prod.yml ps celery-worker

# View Celery logs
docker compose -f docker-compose.prod.yml logs celery-worker

# Verify Redis connection
docker compose -f docker-compose.prod.yml exec celery-worker celery -A config inspect active

# Restart Celery
docker compose -f docker-compose.prod.yml restart celery-worker
```

### Problem: WebSocket Not Working

**Solution**:
```bash
# Verify Redis is running (Channels uses Redis)
docker compose -f docker-compose.prod.yml ps redis

# Verify Channels configuration
docker compose -f docker-compose.prod.yml exec backend python manage.py shell -c "from channels.layers import get_channel_layer; print(get_channel_layer())"

# Verify backend logs
docker compose -f docker-compose.prod.yml logs backend | grep -i websocket
```

### Problem: Static Files Not Loading

**Solution**:
```bash
# Collect static files
docker compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput

# Verify volume is mounted
docker compose -f docker-compose.prod.yml exec nginx ls -la /var/www/static/

# Restart nginx
docker compose -f docker-compose.prod.yml restart nginx
```

### Problem: High Memory Usage

**Solution**:
```bash
# View resource usage
docker stats

# Adjust limits in docker-compose.prod.yml
# Reduce Celery concurrency
# Restart services
docker compose -f docker-compose.prod.yml restart
```

---

## Useful Commands

### Container Management

```bash
# View status of all services
docker compose -f docker-compose.prod.yml ps

# View logs in real time
docker compose -f docker-compose.prod.yml logs -f

# Execute command in container
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
docker compose -f docker-compose.prod.yml exec backend python manage.py dbshell
```

### Database

```bash
# Access PostgreSQL
docker compose -f docker-compose.prod.yml exec db psql -U intell_user -d intell

# Manual backup
docker compose -f docker-compose.prod.yml exec db pg_dump -U intell_user intell > backup.sql

# Manual restore
docker compose -f docker-compose.prod.yml exec -T db psql -U intell_user intell < backup.sql
```

### Django

```bash
# Create superuser
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Run migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create migrations
docker compose -f docker-compose.prod.yml exec backend python manage.py makemigrations

# Django shell
docker compose -f docker-compose.prod.yml exec backend python manage.py shell
```

---

## Additional Security

### Configure Automatic Backups

Add to crontab:

```bash
crontab -e

# Daily backup at 2 AM
0 2 * * * cd /opt/intell/infrastructure && ./backup-db.sh --cleanup >> /var/log/intell-backup.log 2>&1
```

### Log Monitoring

Consider configuring log rotation and monitoring:

```bash
# Configure logrotate for Docker logs
sudo nano /etc/logrotate.d/docker-containers
```

### Security Updates

```bash
# Update system regularly
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

---

## Support

For problems or questions:
1. Review logs: `docker compose -f docker-compose.prod.yml logs`
2. Verify configuration: `docker compose -f docker-compose.prod.yml config`
3. Consult this documentation
4. Contact the development team

---

## Final Notes

- **Never** commit `.docker.env` or `.django.env` files to the repository
- **Always** make a backup before updating
- **Monitor** logs regularly
- **Keep** the system and Docker images updated
- **Review** backups periodically
- **Use `--env-file .docker.env`** in all `docker compose` commands to ensure variables are loaded correctly
- **nginx.conf** is the configuration file used in production (not `nginx.conf.local`)

## Available Scripts

For more information about deployment scripts, see [c-DEPLOYMENT_SCRIPTS.md](c-DEPLOYMENT_SCRIPTS.md).

Good luck with your deployment!
