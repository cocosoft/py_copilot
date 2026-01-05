#!/bin/bash

# PyCopilot Production Environment Start Script
set -e

echo "🚀 Starting PyCopilot Production Environment..."

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

# Check if production environment file exists
if [ ! -f ".env.production" ]; then
    print_error ".env.production file not found. Please create it before starting production."
    exit 1
fi

# Check if required environment variables are set
source .env.production

required_vars=("DATABASE_URL" "SECRET_KEY" "OPENAI_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ] || [[ "${!var}" == *"your-"* ]]; then
        print_error "Required environment variable $var is not properly set."
        exit 1
    fi
done

print_status "Environment validation passed"

# Set production profile
export COMPOSE_PROFILES=production

# Build and start all services
print_status "Building and starting production services..."
docker-compose --profile production up -d --build

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Health check
print_status "Performing health checks..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_status "✅ Backend is healthy"
else
    print_warning "⚠️ Backend health check failed"
fi

# Check frontend health
if curl -f http://localhost:80/health > /dev/null 2>&1; then
    print_status "✅ Frontend is healthy"
else
    print_warning "⚠️ Frontend health check failed"
fi

print_status "🎉 Production environment is ready!"
print_status "Services available at:"
echo "  - Application: http://localhost"
echo "  - API: http://localhost/api"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"

print_status "To view logs: docker-compose --profile production logs -f"
print_status "To stop: docker-compose --profile production down"