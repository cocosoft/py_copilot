#!/bin/bash

# PyCopilot Build Script
set -e

echo "🚀 Starting PyCopilot Build Process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Set environment
ENVIRONMENT=${1:-development}
print_status "Building for environment: $ENVIRONMENT"

# Create environment file
if [ "$ENVIRONMENT" = "production" ]; then
    if [ ! -f ".env.production" ]; then
        print_warning "Production environment file not found. Using default .env.production"
    fi
    cp .env.production .env
    export COMPOSE_PROFILES=production
else
    if [ ! -f ".env.development" ]; then
        print_warning "Development environment file not found. Creating default .env.development"
        cp .env.example .env.development 2>/dev/null || echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/py_copilot" > .env.development
    fi
    cp .env.development .env
fi

# Build backend
print_status "Building backend..."
docker build -f Dockerfile.backend -t py-copilot-backend:latest ./backend

# Build frontend
print_status "Building frontend..."
docker build -f Dockerfile.frontend -t py-copilot-frontend:latest ./frontend

# Build full application
print_status "Building complete application..."
docker build -t py-copilot:latest .

print_status "✅ Build completed successfully!"

# Show image sizes
print_status "Image sizes:"
docker images | grep py-copilot

echo ""
print_status "Next steps:"
echo "1. To start development: ./scripts/start-dev.sh"
echo "2. To start production: ./scripts/start-prod.sh"
echo "3. To view logs: docker-compose logs -f"