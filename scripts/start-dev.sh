#!/bin/bash

# PyCopilot Development Environment Start Script
set -e

echo "🚀 Starting PyCopilot Development Environment..."

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

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
    else
        print_warning "Creating basic .env file..."
        cat > .env << EOF
# Development Environment
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/py_copilot
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=true
API_V1_STR=/api/v1
PROJECT_NAME=PyCopilot
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]
EOF
    fi
fi

# Start development services
print_status "Starting database and cache services..."
docker-compose up -d postgres redis

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend python -m alembic upgrade head

print_status "✅ Development environment is ready!"
print_status "Services available at:"
echo "  - Backend API: http://localhost:8000"
echo "  - API Documentation: http://localhost:8000/docs"
echo "  - Frontend: http://localhost:3000"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"

print_status "To start all services including frontend: docker-compose up"
print_status "To view logs: docker-compose logs -f"