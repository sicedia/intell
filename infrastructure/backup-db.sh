#!/bin/bash
# =============================================================================
# Database Backup Script for Intelli
# Creates timestamped backups of PostgreSQL database
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Backup directory
BACKUP_DIR="$SCRIPT_DIR/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/intell_backup_$TIMESTAMP.sql"
BACKUP_FILE_COMPRESSED="$BACKUP_FILE.gz"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Load environment variables
if [ -f ".docker.env" ]; then
    set -a
    source .docker.env
    set +a
else
    echo -e "${RED}Error: .docker.env file not found${NC}"
    exit 1
fi

# Default values
POSTGRES_DB=${POSTGRES_DB:-intell}
POSTGRES_USER=${POSTGRES_USER:-intell_user}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if database container is running
if ! docker compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    echo "Start it with: docker compose -f docker-compose.prod.yml up -d db"
    exit 1
fi

echo "Creating backup..."
echo "Database: $POSTGRES_DB"
echo "User: $POSTGRES_USER"
echo "Backup file: $BACKUP_FILE_COMPRESSED"
echo ""

# Create backup
docker compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    --clean \
    --if-exists \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE_COMPRESSED"

if [ $? -eq 0 ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE_COMPRESSED" | cut -f1)
    echo -e "${GREEN}Backup created successfully!${NC}"
    echo "File: $BACKUP_FILE_COMPRESSED"
    echo "Size: $BACKUP_SIZE"
    echo ""
    
    # List recent backups
    echo "Recent backups:"
    ls -lht "$BACKUP_DIR"/*.sql.gz 2>/dev/null | head -5 || echo "No previous backups found"
    echo ""
    
    # Optional: Clean old backups (keep last 30 days)
    if [ "$1" == "--cleanup" ]; then
        echo "Cleaning up backups older than 30 days..."
        find "$BACKUP_DIR" -name "intell_backup_*.sql.gz" -mtime +30 -delete
        echo "Cleanup complete"
    else
        echo "To clean old backups (older than 30 days), run:"
        echo "  $0 --cleanup"
    fi
else
    echo -e "${RED}Error: Backup failed${NC}"
    rm -f "$BACKUP_FILE_COMPRESSED"
    exit 1
fi

echo ""
echo "To restore a backup:"
echo "  ./restore-db.sh $BACKUP_FILE_COMPRESSED"
