# PowerShell setup script for Intelli infrastructure
# This script initializes the infrastructure from scratch

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Intelli Infrastructure Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker and docker-compose are available" -ForegroundColor Green
} catch {
    Write-Host "❌ docker-compose not found. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    docker info | Out-Null
} catch {
    Write-Host "❌ Docker is not running. Please start Docker." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Stop any existing containers
Write-Host "Stopping existing containers..."
try {
    docker-compose down -v 2>$null
} catch {
    # Ignore errors if containers don't exist
}

# Start infrastructure services
Write-Host ""
Write-Host "Starting infrastructure services..."
docker-compose up -d

# Wait for PostgreSQL to be ready
Write-Host ""
Write-Host "Waiting for PostgreSQL to be ready..."
$maxAttempts = 30
$attempt = 0
$postgresReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        docker-compose exec -T db pg_isready -U intell_user -d intell 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ PostgreSQL is ready!" -ForegroundColor Green
            $postgresReady = $true
            break
        }
    } catch {
        # Continue waiting
    }
    $attempt++
    Write-Host "   Attempt $attempt/$maxAttempts : Waiting for PostgreSQL..."
    Start-Sleep -Seconds 2
}

if (-not $postgresReady) {
    Write-Host "❌ PostgreSQL failed to start after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Wait for Redis to be ready
Write-Host ""
Write-Host "Waiting for Redis to be ready..."
$attempt = 0
$redisReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        docker-compose exec -T redis redis-cli ping 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Redis is ready!" -ForegroundColor Green
            $redisReady = $true
            break
        }
    } catch {
        # Continue waiting
    }
    $attempt++
    Write-Host "   Attempt $attempt/$maxAttempts : Waiting for Redis..."
    Start-Sleep -Seconds 2
}

if (-not $redisReady) {
    Write-Host "❌ Redis failed to start after $maxAttempts attempts" -ForegroundColor Red
    exit 1
}

# Verify database exists
Write-Host ""
Write-Host "Verifying database setup..."
try {
    docker-compose exec -T db psql -U intell_user -d intell -c "SELECT 1;" 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database 'intell' is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Warning: Could not verify database access" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✅ Infrastructure setup completed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services are running:"
Write-Host "  - PostgreSQL: localhost:5432"
Write-Host "  - Redis: localhost:6379"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Configure backend/.env file (copy from env.development.example)"
Write-Host "  2. Run backend setup: cd ../backend && python scripts/setup_dev.py"
Write-Host "  3. Start Django: python manage.py runserver"
Write-Host ""

