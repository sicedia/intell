#!/bin/bash
# Start Celery worker for development
# This script starts a Celery worker that processes tasks from Redis queues

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Change to backend directory
cd "$BACKEND_DIR"

# Check if Redis is running
echo "Checking Redis connection..."
if ! python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" 2>/dev/null; then
    echo "❌ Error: Redis is not running or not accessible."
    echo "   Please start Redis with: cd infrastructure && docker-compose up -d redis"
    exit 1
fi

echo "✅ Redis is running"

# Start Celery worker
echo ""
echo "Starting Celery worker..."
echo "Queues: ingestion_io, charts_cpu, ai"
echo "Note: Using 'prefork' pool (default on Linux/macOS for parallel execution)"
echo ""

# On Linux/macOS, use default prefork pool (configured in config/celery.py)
# This provides parallel task execution with multiple worker processes
celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
