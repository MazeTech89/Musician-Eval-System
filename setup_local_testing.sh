#!/bin/bash
# Local Testing Setup Script
# Quickly sets up and runs the S3 file upload tests

set -e

echo "================================"
echo "Musician Evaluation System"
echo "Local Testing Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo -e "${GREEN}✓ Docker found${NC}"

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo -e "${YELLOW}❌ Docker Compose is not installed${NC}"
    echo "Please ensure Docker Desktop is installed with Compose support"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose found${NC}"
echo ""

# Copy environment file
if [ ! -f ".env.local" ]; then
    echo -e "${BLUE}📝 Creating .env.local from template${NC}"
    cp backend/.env.example .env.local
    echo "⚠️  Update .env.local if needed"
else
    echo -e "${GREEN}✓ .env.local already exists${NC}"
fi
echo ""

# Check if services are already running
BACKEND_RUNNING=$(docker ps --format '{{.Names}}' | grep -c "musician_eval_backend" || true)

if [ "$BACKEND_RUNNING" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Services are already running${NC}"
    read -p "Do you want to restart them? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Stopping existing services...${NC}"
        docker compose down
    else
        echo "Using existing services"
        EXISTING=true
    fi
fi

if [ "$EXISTING" != "true" ]; then
    # Start services
    echo -e "${BLUE}🚀 Starting services (this may take a few minutes on first run)${NC}"
    echo ""
    docker compose up -d --build

    echo ""
    echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"

    # Wait for PostgreSQL
    echo "  Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker compose exec -T postgres pg_isready -U user >/dev/null 2>&1; then
            echo -e "    ${GREEN}✓ PostgreSQL ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for Redis
    echo "  Waiting for Redis..."
    for i in {1..30}; do
        if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
            echo -e "    ${GREEN}✓ Redis ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for MinIO
    echo "  Waiting for MinIO..."
    for i in {1..30}; do
        if curl -f http://localhost:9000/minio/health/live >/dev/null 2>&1; then
            echo -e "    ${GREEN}✓ MinIO ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for Backend
    echo "  Waiting for Backend API..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/v1/health >/dev/null 2>&1; then
            echo -e "    ${GREEN}✓ Backend API ready${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done

    echo ""
    echo -e "${GREEN}✓ All services are healthy${NC}"
    echo ""
fi

# Create test audio file if it doesn't exist
if [ ! -f "test_audio.wav" ]; then
    echo -e "${BLUE}📁 Creating test audio file...${NC}"
    # Try to create a simple WAV file using Python
    python3 << 'EOF'
import wave
import struct

sample_rate = 44100
duration_ms = 100
num_samples = int(sample_rate * duration_ms / 1000)

with wave.open("test_audio.wav", "w") as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    silence = struct.pack("<h", 0) * num_samples
    wav_file.writeframes(silence)

print("✓ Test audio file created: test_audio.wav")
EOF
fi

echo ""
echo -e "${BLUE}📋 Available Services:${NC}"
echo "  • Backend API: http://localhost:8000"
echo "  • Frontend: http://localhost:5173"
echo "  • MinIO Console: http://localhost:9001 (minioadmin/minioadmin)"
echo "  • Database: localhost:5432 (user/password)"
echo "  • Redis: localhost:6379"
echo ""

# Install test dependencies
echo -e "${BLUE}📦 Installing test dependencies...${NC}"
pip install -q python-dotenv requests >/dev/null 2>&1
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Run the test suite
echo -e "${BLUE}🧪 Running S3 File Upload Test Suite...${NC}"
echo ""

python3 test_s3_local.py

TEST_EXIT_CODE=$?

echo ""
echo "================================"

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Visit MinIO: http://localhost:9001"
    echo "  2. Check uploaded files in the bucket"
    echo "  3. Run frontend tests at http://localhost:5173"
    echo "  4. Review logs: docker compose logs -f backend"
else
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check service logs: docker compose logs"
    echo "  2. Verify connectivity: curl http://localhost:8000/api/v1/health"
    echo "  3. Check database: docker compose exec postgres psql -U user -d musician_eval -c \"SELECT 1\""
    echo "  4. Review LOCAL_TESTING.md for more info"
fi

echo "================================"
exit $TEST_EXIT_CODE
