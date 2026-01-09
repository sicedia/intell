# Start Celery worker for development
# This script starts a Celery worker that processes tasks from Redis queues

$ErrorActionPreference = "Stop"

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

# Change to backend directory
Set-Location $BackendDir

# Check if Redis is running
Write-Host "Checking Redis connection..." -ForegroundColor Cyan
try {
    python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping()" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Redis connection failed"
    }
    Write-Host "✅ Redis is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Redis is not running or not accessible." -ForegroundColor Red
    Write-Host "   Please start Redis with: cd infrastructure && docker-compose up -d redis" -ForegroundColor Yellow
    exit 1
}

# Start Celery worker
Write-Host ""
Write-Host "Starting Celery worker..." -ForegroundColor Cyan
Write-Host "Queues: ingestion_io, charts_cpu, ai" -ForegroundColor Cyan
Write-Host ""

# Note: config/celery.py automatically detects Windows and uses 'solo' pool
# On Linux/production, 'prefork' pool is used by default for better performance
celery -A config worker -l info -Q ingestion_io,charts_cpu,ai
