#!/bin/bash
# =============================================================================
# Production Deployment Script for Intelli
# Ubuntu 24.04 LTS
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Intelli Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}Error: Please do not run this script as root${NC}"
   echo "Run as a regular user with sudo privileges"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh"
    echo "  sudo sh get-docker.sh"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

# Check for required files
if [ ! -f ".docker.env" ]; then
    echo -e "${YELLOW}Warning: .docker.env file not found${NC}"
    echo "Creating .docker.env from .docker.env.example..."
    if [ -f ".docker.env.example" ]; then
        cp .docker.env.example .docker.env
        echo -e "${YELLOW}Please edit .docker.env with your production values before continuing${NC}"
        echo "Press Enter to continue after editing, or Ctrl+C to abort..."
        read
    else
        echo -e "${RED}Error: .docker.env.example not found${NC}"
        exit 1
    fi
fi

if [ ! -f ".django.env" ]; then
    echo -e "${YELLOW}Warning: .django.env file not found${NC}"
    echo "Creating .django.env from .django.env.example..."
    if [ -f ".django.env.example" ]; then
        cp .django.env.example .django.env
        echo -e "${YELLOW}Please edit .django.env with your production values before continuing${NC}"
        echo "See ../ENV_SETUP.md for detailed instructions"
        echo "Press Enter to continue after editing, or Ctrl+C to abort..."
        read
    else
        echo -e "${RED}Error: .django.env.example not found${NC}"
        exit 1
    fi
fi

# Check SSL certificates
if [ ! -f "nginx/ssl/fullchain.pem" ] || [ ! -f "nginx/ssl/privkey.pem" ]; then
    echo -e "${YELLOW}Warning: SSL certificates not found${NC}"
    echo "SSL certificates should be placed in:"
    echo "  - nginx/ssl/fullchain.pem"
    echo "  - nginx/ssl/privkey.pem"
    echo ""
    echo "You can:"
    echo "  1. Run ./setup-ssl.sh to configure Let's Encrypt certificates"
    echo "  2. Or manually copy your certificates to nginx/ssl/"
    echo ""
    read -p "Continue without SSL? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create SSL directory if it doesn't exist
mkdir -p nginx/ssl

# Load environment variables
set -a
source .docker.env
set +a

# Validate required environment variables
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}Error: POSTGRES_PASSWORD is not set in .env${NC}"
    exit 1
fi

echo -e "${GREEN}Starting deployment...${NC}"
echo ""

# Stop existing containers
echo "Stopping existing containers..."
docker compose -f docker-compose.prod.yml down || true

# Build and start services
echo "Building and starting services..."
docker compose -f docker-compose.prod.yml build --no-cache

echo "Starting services..."
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 10

# Check service health
echo "Checking service health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker compose -f docker-compose.prod.yml ps | grep -q "healthy"; then
        echo -e "${GREEN}Services are healthy${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for services... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 5
done

# Run database migrations
echo ""
echo "Running database migrations..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
docker compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# Check if superuser exists
echo "Checking for superuser..."
SUPERUSER_EXISTS=$(docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
print('True' if User.objects.filter(is_superuser=True).exists() else 'False')
" 2>/dev/null | tr -d '\r\n' || echo "False")

if [ "$SUPERUSER_EXISTS" != "True" ]; then
    echo -e "${YELLOW}No superuser found. Creating one...${NC}"
    docker compose -f docker-compose.prod.yml exec -T backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@cedia.org.ec', 'admin')
    print('Superuser created successfully')
else:
    print('User with username admin already exists')
"
else
    echo -e "${GREEN}Superuser already exists${NC}"
fi

# Show service status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service Status:"
docker compose -f docker-compose.prod.yml ps
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.prod.yml logs -f"
echo ""
echo "To stop services:"
echo "  docker compose -f docker-compose.prod.yml down"
echo ""
echo "To restart services:"
echo "  docker compose -f docker-compose.prod.yml restart"
echo ""
