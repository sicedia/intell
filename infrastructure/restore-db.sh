#!/bin/bash
# =============================================================================
# Database Restore Script for Intelli
# Restores a PostgreSQL database from a backup file
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

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Backup file not specified${NC}"
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

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
echo -e "${GREEN}Database Restore${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${RED}WARNING: This will replace all data in the database!${NC}"
echo "Database: $POSTGRES_DB"
echo "Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Check if database container is running
if ! docker compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
    echo -e "${RED}Error: Database container is not running${NC}"
    echo "Start it with: docker compose -f docker-compose.prod.yml up -d db"
    exit 1
fi

echo ""
echo "Restoring database..."

# Restore from compressed backup
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | docker compose -f docker-compose.prod.yml exec -T db psql \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB"
else
    docker compose -f docker-compose.prod.yml exec -T db psql \
        -U "$POSTGRES_USER" \
        -d "$POSTGRES_DB" \
        < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database restored successfully!${NC}"
else
    echo -e "${RED}Error: Restore failed${NC}"
    exit 1
fi
