#!/bin/bash
# Run script for Green-Code FX Docker container
# This script starts the container with proper configuration

set -e  # Exit on any error

# Configuration
IMAGE_NAME="green-code-fx"
TAG="${1:-latest}"
CONTAINER_NAME="green-code-fx-generator"
HOST_PORT="8082"
CONTAINER_PORT="8082"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Green-Code FX container...${NC}"
echo "Image: ${IMAGE_NAME}:${TAG}"
echo "Container: ${CONTAINER_NAME}"
echo "Port: ${HOST_PORT}:${CONTAINER_PORT}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if image exists
if ! docker image inspect "${IMAGE_NAME}:${TAG}" > /dev/null 2>&1; then
    echo -e "${RED}Error: Image ${IMAGE_NAME}:${TAG} not found${NC}"
    echo "Please build the image first:"
    echo "  ./scripts/build.sh"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop "${CONTAINER_NAME}" > /dev/null 2>&1 || true
    docker rm "${CONTAINER_NAME}" > /dev/null 2>&1 || true
fi

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p output temp assets/fonts

# Run the container
echo -e "${YELLOW}Starting container...${NC}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    -v "$(pwd)/output:/app/output:rw" \
    -v "$(pwd)/assets:/app/assets:ro" \
    -v "$(pwd)/temp:/app/temp:rw" \
    -e SDL_VIDEODRIVER=dummy \
    -e PYTHONUNBUFFERED=1 \
    -e FLASK_ENV=production \
    "${IMAGE_NAME}:${TAG}"

# Wait a moment for container to start
sleep 3

# Check if container is running
if docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${GREEN}Container started successfully!${NC}"
    echo ""
    echo "Container status:"
    docker ps --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    echo "API endpoints:"
    echo "  Health check: http://localhost:${HOST_PORT}/api/health"
    echo "  Generate typing: POST http://localhost:${HOST_PORT}/api/generate/typing"
    echo "  Generate matrix: POST http://localhost:${HOST_PORT}/api/generate/matrix"
    echo ""
    echo "To view logs:"
    echo "  docker logs -f ${CONTAINER_NAME}"
    echo ""
    echo "To stop the container:"
    echo "  docker stop ${CONTAINER_NAME}"
else
    echo -e "${RED}Failed to start container!${NC}"
    echo "Container logs:"
    docker logs "${CONTAINER_NAME}"
    exit 1
fi
