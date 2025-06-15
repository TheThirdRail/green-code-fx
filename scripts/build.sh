#!/bin/bash
# Build script for Green-Code FX Docker container
# This script builds the Docker image with proper caching and optimization

set -e  # Exit on any error

# Configuration
IMAGE_NAME="green-code-fx"
TAG="${1:-latest}"
DOCKERFILE="Dockerfile"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Green-Code FX Docker image...${NC}"
echo "Image: ${IMAGE_NAME}:${TAG}"
echo "Dockerfile: ${DOCKERFILE}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "${DOCKERFILE}" ]; then
    echo -e "${RED}Error: ${DOCKERFILE} not found${NC}"
    exit 1
fi

# Build the image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build \
    --tag "${IMAGE_NAME}:${TAG}" \
    --file "${DOCKERFILE}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

# Check build success
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo ""
    echo "Image details:"
    docker images "${IMAGE_NAME}:${TAG}"
    echo ""
    echo "To run the container:"
    echo "  docker-compose up -d"
    echo ""
    echo "To test the container:"
    echo "  docker run --rm -p 8082:8082 ${IMAGE_NAME}:${TAG}"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi
