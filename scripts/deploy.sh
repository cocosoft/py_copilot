#!/bin/bash

# PyCopilot Deployment Script
set -e

echo "🚀 Deploying PyCopilot to production..."

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

# Configuration
IMAGE_TAG=${1:-latest}
REGISTRY=${DOCKER_REGISTRY:-your-registry.com/py-copilot}
CONTAINER_NAME=py-copilot

# Validate environment
if [ -z "$DOCKER_REGISTRY" ]; then
    print_warning "DOCKER_REGISTRY not set. Using default registry."
fi

# Build and tag images
print_status "Building and tagging images with tag: $IMAGE_TAG"
docker build -f Dockerfile.backend -t $REGISTRY/backend:$IMAGE_TAG ./backend
docker build -f Dockerfile.frontend -t $REGISTRY/frontend:$IMAGE_TAG ./frontend
docker build -t $REGISTRY/app:$IMAGE_TAG .

# Push images to registry
print_status "Pushing images to registry..."
docker push $REGISTRY/backend:$IMAGE_TAG
docker push $REGISTRY/frontend:$IMAGE_TAG
docker push $REGISTRY/app:$IMAGE_TAG

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Pull latest images
print_status "Pulling latest images..."
docker pull $REGISTRY/app:$IMAGE_TAG

# Start with new images
print_status "Starting new containers..."
docker-compose up -d

# Wait for deployment to stabilize
print_status "Waiting for deployment to stabilize..."
sleep 30

# Health check
print_status "Performing health check..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_status "✅ Deployment successful!"
else
    print_error "❌ Deployment failed. Rolling back..."
    docker-compose down
    # Implement rollback logic here if needed
    exit 1
fi

print_status "🎉 Deployment completed successfully!"
print_status "Application available at: http://localhost"