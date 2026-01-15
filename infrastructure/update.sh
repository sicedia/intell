#!/bin/bash
# =============================================================================
# Update Script for Intelli Production
# Pulls latest code, rebuilds containers, and restarts services
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Intelli Production Update${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if git repository
if [ -d "../.git" ]; then
    echo -e "${BLUE}Pulling latest code...${NC}"
    cd ..
    git pull
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}Code updated${NC}"
    echo ""
else
    echo -e "${YELLOW}Not a git repository, skipping code pull${NC}"
    echo ""
fi

# Ask for confirmation
read -p "This will rebuild and restart all services. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Update cancelled"
    exit 0
fi

# Create backup before update
echo ""
echo -e "${BLUE}Creating database backup...${NC}"
if [ -f "backup-db.sh" ]; then
    ./backup-db.sh || echo -e "${YELLOW}Warning: Backup failed, continuing anyway...${NC}"
else
    echo -e "${YELLOW}Warning: backup-db.sh not found, skipping backup${NC}"
fi
echo ""

# Stop services
echo -e "${BLUE}Stopping services...${NC}"
docker-compose -f docker-compose.prod.yml down

# Rebuild images
echo -e "${BLUE}Rebuilding images...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
echo -e "${BLUE}Starting services...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
echo "Waiting for services to be healthy..."
sleep 10

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py migrate --noinput

# Collect static files
echo -e "${BLUE}Collecting static files...${NC}"
docker-compose -f docker-compose.prod.yml exec -T backend python manage.py collectstatic --noinput

# Show status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f"
