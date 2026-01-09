#!/bin/bash
# Setup script for Intelli infrastructure
# This script initializes the infrastructure from scratch

set -e  # Exit on error

echo "=========================================="
echo "  Intelli Infrastructure Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running. Please start Docker.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and docker-compose are available${NC}"
echo ""

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose down -v 2>/dev/null || true

# Start infrastructure services
echo ""
echo "Starting infrastructure services..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T db pg_isready -U intell_user -d intell &> /dev/null; then
        echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts: Waiting for PostgreSQL..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ PostgreSQL failed to start after $max_attempts attempts${NC}"
    exit 1
fi

# Wait for Redis to be ready
echo ""
echo "Waiting for Redis to be ready..."
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec -T redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis is ready!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "   Attempt $attempt/$max_attempts: Waiting for Redis..."
    sleep 2
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}❌ Redis failed to start after $max_attempts attempts${NC}"
    exit 1
fi

# Verify database exists
echo ""
echo "Verifying database setup..."
if docker-compose exec -T db psql -U intell_user -d intell -c "SELECT 1;" &> /dev/null; then
    echo -e "${GREEN}✅ Database 'intell' is accessible${NC}"
else
    echo -e "${YELLOW}⚠️  Warning: Could not verify database access${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Infrastructure setup completed!${NC}"
echo "=========================================="
echo ""
echo "Services are running:"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "Next steps:"
echo "  1. Configure backend/.env file (copy from env.example)"
echo "  2. Run backend setup: cd ../backend && python scripts/setup_dev.py"
echo "  3. Start Django: python manage.py runserver"
echo ""

