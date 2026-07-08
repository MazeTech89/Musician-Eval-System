# Local Testing Guide - S3 File Upload

## Overview

This guide walks you through testing the S3 file upload functionality locally using MinIO (S3-compatible storage).

**What You'll Test:**
- Database connectivity
- API health check
- User registration & login
- Performance creation
- Audio file upload to MinIO
- File metadata retrieval
- Invalid file rejection
- Large file rejection

## Prerequisites

### 1. Install Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt
pip install python-dotenv requests  # For testing

# Frontend dependencies (if testing UI)
cd ../frontend
npm install
```

### 2. Install Docker & Docker Compose

Verify installation:
```bash
docker --version
docker compose --version
```

## Quick Start (5 minutes)

### Step 1: Start Services

```bash
cd /path/to/Musician-Eval-System

# Start all services (PostgreSQL, Redis, MinIO, Backend, Frontend)
docker compose up --build

# Wait for all services to be healthy (watch terminal output)
# - PostgreSQL should be ready
# - Redis should respond to ping
# - MinIO should be healthy
# - Backend should start on port 8000
# - Frontend should start on port 5173
```

**First Time Tips:**
- Building images takes 2-3 minutes on first run
- Use `-d` flag to run in background: `docker compose up -d --build`
- View logs: `docker compose logs -f backend`

### Step 2: Run Test Suite

In a new terminal:

```bash
# Navigate to project root
cd /path/to/Musician-Eval-System

# Install test dependencies
pip install python-dotenv requests

# Run tests
python test_s3_local.py
```

**Expected Output:**
```
============================================================
  Musician Evaluation System - Local Testing Suite
============================================================

Created test audio file: test_audio.wav

============================================================
  1. Testing API Health
============================================================

✓ API is healthy
  Response: {'status': 'ok'}

============================================================
  2. Registering Test User
============================================================

✓ User registered successfully
  User: testmusician

...

Total: 8/8 tests passed
```

### Step 3: Verify MinIO Upload

Access MinIO console to verify files were uploaded:

```
URL: http://localhost:9001
Username: minioadmin
Password: minioadmin
```

**What to look for:**
- Bucket: `development-musician-eval-uploads`
- Objects in: `performances/<performance_id>/`
- Each upload creates a timestamped file

## Manual Testing

### 1. Register User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "TestPass123!"
  }'

# Save the access_token from response
export TOKEN="your-token-here"
```

### 3. Create Performance

```bash
curl -X POST http://localhost:8000/api/v1/performances \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Performance",
    "description": "A test performance",
    "audio_file_url": null
  }'

# Save the id from response
export PERF_ID=1
```

### 4. Upload Audio File

```bash
# Create a test audio file
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 test_audio.wav

# Upload it
curl -X POST http://localhost:8000/api/v1/performances/$PERF_ID/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_audio.wav"
```

### 5. Get Performance with File Info

```bash
curl -X GET http://localhost:8000/api/v1/performances/$PERF_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq .
```

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Backend API | http://localhost:8000 | N/A |
| Frontend | http://localhost:5173 | Login with test user |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| PostgreSQL | localhost:5432 | user / password |
| Redis | localhost:6379 | N/A |

## Viewing Logs

### Backend Logs
```bash
docker compose logs -f backend

# Follow specific service
docker compose logs -f backend --tail 50
```

### Database Logs
```bash
docker compose logs -f postgres
```

### MinIO Logs
```bash
docker compose logs -f minio
```

## Database Operations

### Connect to Database

```bash
# Via psql
psql postgresql://user:password@localhost:5432/musician_eval

# Or using docker compose
docker compose exec postgres psql -U user -d musician_eval
```

### Useful Queries

```sql
-- View all performances
SELECT id, title, audio_s3_key, file_size_bytes, uploaded_at FROM performances;

-- View specific performance with uploads
SELECT * FROM performances WHERE id = 1;

-- Check file metadata
SELECT id, musician_id, audio_s3_key, file_size_bytes, uploaded_at 
FROM performances 
WHERE audio_s3_key IS NOT NULL;

-- Delete test data
DELETE FROM performances WHERE title = 'Test Performance';
DELETE FROM "user" WHERE username = 'testuser';
```

## Troubleshooting

### Backend Won't Start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Port 8000 already in use
#    Kill process: lsof -ti:8000 | xargs kill -9

# 2. Database not ready
#    Wait 10 seconds and retry: docker compose up

# 3. Database migration issues
#    Rebuild: docker compose down -v && docker compose up --build
```

### MinIO Errors

```bash
# MinIO won't connect
# Check if port 9000 is in use
lsof -i :9000

# Reset MinIO data
docker compose down -v
docker compose up -d minio

# Wait for health check
docker compose exec minio mc ready local
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker compose exec postgres pg_isready

# Verify credentials in DATABASE_URL
# Default: postgresql://user:password@postgres:5432/musician_eval

# Check database exists
docker compose exec postgres psql -U user -l
```

### Files Not Uploading

```bash
# Check S3 endpoint
curl -v http://localhost:9000

# Check MinIO bucket exists
docker compose exec minio mc ls local/

# Check IAM credentials in backend env
docker compose exec backend env | grep AWS
```

## Testing File Validation

### Valid File Upload
```bash
# Create valid audio
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 valid.wav
curl -X POST http://localhost:8000/api/v1/performances/1/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@valid.wav"
```

### Invalid Format (Should Fail)
```bash
# Create text file
echo "Not audio" > invalid.txt
curl -X POST http://localhost:8000/api/v1/performances/1/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invalid.txt"
# Expected: 400 Bad Request
```

### Too Large File (Should Fail)
```bash
# Create 60MB file (exceeds 50MB limit)
dd if=/dev/zero of=large.wav bs=1M count=60
curl -X POST http://localhost:8000/api/v1/performances/1/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@large.wav"
# Expected: 400 Bad Request - File size exceeds maximum limit
```

## Performance Testing

### Load Test File Upload

```bash
# Create test script
cat > load_test.sh << 'EOF'
#!/bin/bash
for i in {1..10}; do
  echo "Upload $i..."
  curl -X POST http://localhost:8000/api/v1/performances/1/upload-audio \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test_audio.wav" \
    -o /dev/null -s -w "%{http_code}\n"
done
EOF

bash load_test.sh
```

### Monitor Resource Usage

```bash
docker compose stats

# Watch memory/CPU usage of backend
docker stats musician_eval_backend
```

## Cleanup

### Stop Services
```bash
# Stop but keep data
docker compose stop

# Stop and remove containers
docker compose down

# Stop, remove containers, and delete volumes
docker compose down -v
```

### Clean Local Files
```bash
# Remove test files
rm -f test_audio.wav test_invalid.txt large.wav

# Remove test database
rm -rf backend/tmp_pgdata/
rm -rf backend/alembic/versions/__pycache__/
```

## Advanced Testing

### Test with Curl

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "username": "curluser",
  "email": "curl@test.com",
  "password": "CurlPass123!",
  "first_name": "Curl",
  "last_name": "User"
}
EOF

# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"curluser","password":"CurlPass123!"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Create performance and upload
PERF=$(curl -s -X POST http://localhost:8000/api/v1/performances \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Curl Test","description":"Test"}' \
  | grep -o '"id":[0-9]*' | grep -o '[0-9]*')

echo "Performance ID: $PERF"

# Upload file
curl -X POST http://localhost:8000/api/v1/performances/$PERF/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_audio.wav"
```

### Test with Python

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register
requests.post(f"{BASE_URL}/auth/register", json={
    "username": "pyuser",
    "email": "py@test.com",
    "password": "PyPass123!",
    "first_name": "Python",
    "last_name": "User"
})

# Login
token_resp = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "pyuser",
    "password": "PyPass123!"
})
token = token_resp.json()["access_token"]

# Create performance
perf_resp = requests.post(f"{BASE_URL}/performances", 
    headers={"Authorization": f"Bearer {token}"},
    json={"title": "Python Test", "description": "Test"}
)
perf_id = perf_resp.json()["id"]

# Upload file
with open("test_audio.wav", "rb") as f:
    files = {"file": ("test.wav", f, "audio/wav")}
    upload_resp = requests.post(
        f"{BASE_URL}/performances/{perf_id}/upload-audio",
        headers={"Authorization": f"Bearer {token}"},
        files=files
    )
    print(upload_resp.json())
```

## Next Steps

After successful local testing:

1. **Test the UI**
   - Navigate to http://localhost:5173
   - Register, login, submit performance
   - Upload audio file through the UI

2. **Review MinIO Storage**
   - Check http://localhost:9001
   - Verify files in bucket
   - Download signed URL

3. **Test Database**
   - Connect to PostgreSQL
   - Verify metadata storage
   - Check indices and performance

4. **Prepare AWS Deployment**
   - Build Docker images for ECR
   - Test terraform plan
   - Prepare production environment

## Support

### Check Logs
```bash
# All services
docker compose logs

# Specific service
docker compose logs -f backend

# With timestamps
docker compose logs -t
```

### Debug API
```bash
# Check if API is responding
curl -v http://localhost:8000/api/v1/health

# Check CORS headers
curl -v -X OPTIONS http://localhost:8000/api/v1/performances

# Get detailed error
curl -v http://localhost:8000/api/v1/nonexistent
```

### Performance Monitoring
```bash
# Monitor backend performance
docker compose exec backend python -m cProfile -s cumtime test_s3_local.py

# Database query analysis
docker compose exec postgres psql -U user -d musician_eval -c "ANALYZE;"
```

---

**Happy Testing!** 🚀

For issues or questions, check the implementation at `AWS_S3_IMPLEMENTATION.md` and `DEPLOYMENT_GUIDE.md`.
