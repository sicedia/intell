#!/bin/bash
# =============================================================================
# Build Docker Images Locally (without push)
# Usage: ./build-local.sh [VERSION_TAG]
# Example: ./build-local.sh v1.0.1
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Docker registry
DOCKER_REGISTRY="sicedia"

# Get version tag from argument or use 'latest'
VERSION_TAG=${1:-latest}

# If version tag doesn't start with 'v', add it
if [[ ! $VERSION_TAG =~ ^v ]]; then
    VERSION_TAG="v${VERSION_TAG}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Docker Images Locally${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Registry:${NC} ${DOCKER_REGISTRY}"
echo -e "${BLUE}Version Tag:${NC} ${VERSION_TAG}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if .build.env exists for frontend build args
BUILD_ENV_FILE="${SCRIPT_DIR}/.build.env"
if [ ! -f "$BUILD_ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: .build.env file not found${NC}"
    echo "Creating .build.env from .build.env.example..."
    if [ -f "${SCRIPT_DIR}/.build.env.example" ]; then
        cp "${SCRIPT_DIR}/.build.env.example" "$BUILD_ENV_FILE"
        echo -e "${YELLOW}Please edit .build.env with your production values${NC}"
        echo "Press Enter to continue after editing, or Ctrl+C to abort..."
        read
    else
        echo -e "${RED}Error: .build.env.example not found${NC}"
        exit 1
    fi
fi

# Load build environment variables from infrastructure/.build.env
set -a
source "$BUILD_ENV_FILE"
set +a

# Also load .env from backend if it exists (for backend-specific vars)
BACKEND_ENV_FILE="${SCRIPT_DIR}/../backend/.env"
if [ -f "$BACKEND_ENV_FILE" ]; then
    echo -e "${BLUE}Loading backend .env file...${NC}"
    set -a
    source "$BACKEND_ENV_FILE"
    set +a
fi

# Also load .env.local from frontend if it exists (for frontend-specific vars)
FRONTEND_ENV_FILE="${SCRIPT_DIR}/../frontend/.env.local"
if [ -f "$FRONTEND_ENV_FILE" ]; then
    echo -e "${BLUE}Loading frontend .env.local file...${NC}"
    set -a
    source "$FRONTEND_ENV_FILE"
    set +a
fi

# Construct URLs from domain if not explicitly set
if [ -z "$NEXT_PUBLIC_API_BASE_URL" ] || [ -z "$NEXT_PUBLIC_WS_BASE_URL" ]; then
    if [ -z "$PRODUCTION_DOMAIN" ]; then
        echo -e "${RED}Error: Either PRODUCTION_DOMAIN or NEXT_PUBLIC_API_BASE_URL/NEXT_PUBLIC_WS_BASE_URL must be set in .build.env${NC}"
        exit 1
    fi
    
    # Construct URLs from domain
    NEXT_PUBLIC_API_BASE_URL="https://${PRODUCTION_DOMAIN}/api"
    NEXT_PUBLIC_WS_BASE_URL="wss://${PRODUCTION_DOMAIN}/ws"
    
    echo -e "${BLUE}Constructed URLs from domain:${NC}"
    echo -e "${BLUE}  API: ${NEXT_PUBLIC_API_BASE_URL}${NC}"
    echo -e "${BLUE}  WS: ${NEXT_PUBLIC_WS_BASE_URL}${NC}"
    echo ""
fi

# Validate required build args
if [ -z "$NEXT_PUBLIC_API_BASE_URL" ] || [ -z "$NEXT_PUBLIC_WS_BASE_URL" ]; then
    echo -e "${RED}Error: NEXT_PUBLIC_API_BASE_URL and NEXT_PUBLIC_WS_BASE_URL must be set${NC}"
    exit 1
fi

# Build Backend Image
echo -e "${GREEN}Building backend image...${NC}"
cd "${SCRIPT_DIR}/../backend"
docker build \
    -f Dockerfile.prod \
    -t "${DOCKER_REGISTRY}/intell-backend:${VERSION_TAG}" \
    -t "${DOCKER_REGISTRY}/intell-backend:latest" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backend image built successfully${NC}"
else
    echo -e "${RED}✗ Backend image build failed${NC}"
    exit 1
fi

# Build Frontend Image
echo ""
echo -e "${GREEN}Building frontend image...${NC}"
cd "${SCRIPT_DIR}/../frontend"
docker build \
    -f Dockerfile.prod \
    --build-arg NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL}" \
    --build-arg NEXT_PUBLIC_WS_BASE_URL="${NEXT_PUBLIC_WS_BASE_URL}" \
    --build-arg NEXT_PUBLIC_APP_ENV="${NEXT_PUBLIC_APP_ENV:-production}" \
    -t "${DOCKER_REGISTRY}/intell-frontend:${VERSION_TAG}" \
    -t "${DOCKER_REGISTRY}/intell-frontend:latest" \
    .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Frontend image built successfully${NC}"
else
    echo -e "${RED}✗ Frontend image build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Images built locally:"
echo "  - ${DOCKER_REGISTRY}/intell-backend:${VERSION_TAG}"
echo "  - ${DOCKER_REGISTRY}/intell-backend:latest"
echo "  - ${DOCKER_REGISTRY}/intell-frontend:${VERSION_TAG}"
echo "  - ${DOCKER_REGISTRY}/intell-frontend:latest"
echo ""
echo "To push these images to Docker Hub, run:"
echo "  ./build-and-push.sh ${VERSION_TAG}"
echo ""
