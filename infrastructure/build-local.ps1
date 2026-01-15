# =============================================================================
# Build Docker Images Locally (without push) - PowerShell
# Usage: .\build-local.ps1 [VERSION_TAG]
# Example: .\build-local.ps1 v1.0.1
# =============================================================================

$ErrorActionPreference = "Stop"

# Script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# Docker registry
$DOCKER_REGISTRY = "sicedia"

# Get version tag from argument or use 'latest'
$VERSION_TAG = if ($args.Count -gt 0) { $args[0] } else { "latest" }

# If version tag doesn't start with 'v', add it
if (-not $VERSION_TAG.StartsWith("v")) {
    $VERSION_TAG = "v$VERSION_TAG"
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Docker Images Locally" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Registry: $DOCKER_REGISTRY" -ForegroundColor Cyan
Write-Host "Version Tag: $VERSION_TAG" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    docker --version | Out-Null
} catch {
    Write-Host "Error: Docker is not installed" -ForegroundColor Red
    exit 1
}

# Check if .build.env exists for frontend build args
$BUILD_ENV_FILE = Join-Path $SCRIPT_DIR ".build.env"
if (-not (Test-Path $BUILD_ENV_FILE)) {
    Write-Host "Warning: .build.env file not found" -ForegroundColor Yellow
    Write-Host "Creating .build.env from .build.env.example..."
    $BUILD_ENV_EXAMPLE = Join-Path $SCRIPT_DIR ".build.env.example"
    if (Test-Path $BUILD_ENV_EXAMPLE) {
        Copy-Item $BUILD_ENV_EXAMPLE $BUILD_ENV_FILE
        Write-Host "Please edit .build.env with your production values" -ForegroundColor Yellow
        Read-Host "Press Enter to continue after editing, or Ctrl+C to abort"
    } else {
        Write-Host "Error: .build.env.example not found" -ForegroundColor Red
        exit 1
    }
}

# Load build environment variables from infrastructure/.build.env
Get-Content $BUILD_ENV_FILE | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim()
        Set-Item -Path "env:$name" -Value $value
    }
}

# Also load .env from backend if it exists (for backend-specific vars)
$BACKEND_ENV_FILE = Join-Path $SCRIPT_DIR "..\backend\.env"
if (Test-Path $BACKEND_ENV_FILE) {
    Write-Host "Loading backend .env file..." -ForegroundColor Cyan
    Get-Content $BACKEND_ENV_FILE | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Also load .env.local from frontend if it exists (for frontend-specific vars)
$FRONTEND_ENV_FILE = Join-Path $SCRIPT_DIR "..\frontend\.env.local"
if (Test-Path $FRONTEND_ENV_FILE) {
    Write-Host "Loading frontend .env.local file..." -ForegroundColor Cyan
    Get-Content $FRONTEND_ENV_FILE | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
        }
    }
}

# Construct URLs from domain if not explicitly set
if (-not $env:NEXT_PUBLIC_API_BASE_URL -or -not $env:NEXT_PUBLIC_WS_BASE_URL) {
    if (-not $env:PRODUCTION_DOMAIN) {
        Write-Host "Error: Either PRODUCTION_DOMAIN or NEXT_PUBLIC_API_BASE_URL/NEXT_PUBLIC_WS_BASE_URL must be set in .build.env" -ForegroundColor Red
        exit 1
    }
    
    # Construct URLs from domain
    $env:NEXT_PUBLIC_API_BASE_URL = "https://$env:PRODUCTION_DOMAIN/api"
    $env:NEXT_PUBLIC_WS_BASE_URL = "wss://$env:PRODUCTION_DOMAIN/ws"
    
    Write-Host "Constructed URLs from domain:" -ForegroundColor Cyan
    Write-Host "  API: $env:NEXT_PUBLIC_API_BASE_URL" -ForegroundColor Cyan
    Write-Host "  WS: $env:NEXT_PUBLIC_WS_BASE_URL" -ForegroundColor Cyan
    Write-Host ""
}

# Validate required build args
if (-not $env:NEXT_PUBLIC_API_BASE_URL -or -not $env:NEXT_PUBLIC_WS_BASE_URL) {
    Write-Host "Error: NEXT_PUBLIC_API_BASE_URL and NEXT_PUBLIC_WS_BASE_URL must be set" -ForegroundColor Red
    exit 1
}

# Build Backend Image
Write-Host "Building backend image..." -ForegroundColor Green
$BACKEND_DIR = Join-Path $SCRIPT_DIR "..\backend"
Set-Location $BACKEND_DIR

docker build `
    -f Dockerfile.prod `
    -t "${DOCKER_REGISTRY}/intell-backend:${VERSION_TAG}" `
    -t "${DOCKER_REGISTRY}/intell-backend:latest" `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Backend image built successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Backend image build failed" -ForegroundColor Red
    exit 1
}

# Build Frontend Image
Write-Host ""
Write-Host "Building frontend image..." -ForegroundColor Green
$FRONTEND_DIR = Join-Path $SCRIPT_DIR "..\frontend"
Set-Location $FRONTEND_DIR

$NEXT_PUBLIC_APP_ENV = if ($env:NEXT_PUBLIC_APP_ENV) { $env:NEXT_PUBLIC_APP_ENV } else { "production" }

docker build `
    -f Dockerfile.prod `
    --build-arg NEXT_PUBLIC_API_BASE_URL="$env:NEXT_PUBLIC_API_BASE_URL" `
    --build-arg NEXT_PUBLIC_WS_BASE_URL="$env:NEXT_PUBLIC_WS_BASE_URL" `
    --build-arg NEXT_PUBLIC_APP_ENV="$NEXT_PUBLIC_APP_ENV" `
    -t "${DOCKER_REGISTRY}/intell-frontend:${VERSION_TAG}" `
    -t "${DOCKER_REGISTRY}/intell-frontend:latest" `
    .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Frontend image built successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Frontend image build failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Images built locally:"
Write-Host "  - ${DOCKER_REGISTRY}/intell-backend:${VERSION_TAG}"
Write-Host "  - ${DOCKER_REGISTRY}/intell-backend:latest"
Write-Host "  - ${DOCKER_REGISTRY}/intell-frontend:${VERSION_TAG}"
Write-Host "  - ${DOCKER_REGISTRY}/intell-frontend:latest"
Write-Host ""
Write-Host "To push these images to Docker Hub, run:"
Write-Host "  .\build-and-push.ps1 ${VERSION_TAG}"
Write-Host ""
