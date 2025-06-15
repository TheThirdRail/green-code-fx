#!/bin/bash
# Health check script for Green-Code FX container
# This script verifies the container is running and API is responding

set -e  # Exit on any error

# Configuration
CONTAINER_NAME="green-code-fx-generator"
API_URL="http://localhost:8082/api/health"
TIMEOUT=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Green-Code FX Health Check${NC}"
echo "Container: ${CONTAINER_NAME}"
echo "API URL: ${API_URL}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running${NC}"
    exit 1
fi

# Check if container exists
if ! docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ Container ${CONTAINER_NAME} not found${NC}"
    echo "Please start the container first:"
    echo "  ./scripts/run.sh"
    exit 1
fi

# Check if container is running
if ! docker ps --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${RED}❌ Container ${CONTAINER_NAME} is not running${NC}"
    echo "Container status:"
    docker ps -a --filter "name=${CONTAINER_NAME}" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    echo "Recent logs:"
    docker logs --tail 20 "${CONTAINER_NAME}"
    exit 1
fi

echo -e "${GREEN}✅ Container is running${NC}"

# Check container health
echo -e "${YELLOW}Checking container health...${NC}"
HEALTH_STATUS=$(docker inspect --format='{{.State.Health.Status}}' "${CONTAINER_NAME}" 2>/dev/null || echo "unknown")
echo "Health status: ${HEALTH_STATUS}"

# Check API endpoint
echo -e "${YELLOW}Testing API endpoint...${NC}"
if command -v curl > /dev/null 2>&1; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time ${TIMEOUT} "${API_URL}" || echo "000")
    
    if [ "${HTTP_CODE}" = "200" ]; then
        echo -e "${GREEN}✅ API is responding (HTTP ${HTTP_CODE})${NC}"
        
        # Get detailed health info
        echo ""
        echo "API Health Response:"
        curl -s --max-time ${TIMEOUT} "${API_URL}" | python -m json.tool 2>/dev/null || echo "Failed to parse JSON response"
    else
        echo -e "${RED}❌ API is not responding (HTTP ${HTTP_CODE})${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  curl not available, skipping API test${NC}"
fi

# Show container stats
echo ""
echo -e "${YELLOW}Container Statistics:${NC}"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "${CONTAINER_NAME}"

# Show recent logs
echo ""
echo -e "${YELLOW}Recent Logs (last 10 lines):${NC}"
docker logs --tail 10 "${CONTAINER_NAME}"

echo ""
echo -e "${GREEN}✅ Health check completed successfully!${NC}"
