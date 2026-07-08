# Quick Reference - Local Testing

## TL;DR - Get Started in 2 Minutes

### Windows
```cmd
setup_local_testing.bat
```

### macOS/Linux
```bash
chmod +x setup_local_testing.sh
./setup_local_testing.sh
```

This will:
1. ✓ Start Docker containers (PostgreSQL, Redis, MinIO, Backend, Frontend)
2. ✓ Create test audio file
3. ✓ Run complete test suite
4. ✓ Show results

---

## Command Cheatsheet

### Start/Stop Services

```bash
# Start all services
docker compose up -d --build

# Stop all services (keep data)
docker compose stop

# Stop and remove containers (keep volumes)
docker compose down

# Stop, remove everything (clean slate)
docker compose down -v

# View logs
docker compose logs -f          # All logs
docker compose logs -f backend  # Backend only
docker compose logs -f minio    # MinIO only
```

### Test Endpoints

```bash
# Health check
curl http://localhost:8000/api/v1/health

# MinIO Console
open http://localhost:9001  # or http://localhost:9001 in browser

# Frontend
open http://localhost:5173  # or http://localhost:5173 in browser
```

### Run Tests

```bash
# Full test suite
python test_s3_local.py

# Or use setup script
./setup_local_testing.sh    # macOS/Linux
setup_local_testing.bat     # Windows
```

### Access Database

```bash
# Connect via psql
psql postgresql://user:password@localhost:5432/musician_eval

# Or via docker
docker compose exec postgres psql -U user -d musician_eval
```

### Access MinIO

**Browser**: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

**CLI**: 
```bash
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local/
mc ls local/development-musician-eval-uploads/
```

---

## File Upload API

### Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "musician1",
    "email": "user@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Musician"
  }'
```

### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "musician1",
    "password": "SecurePass123!"
  }' | jq '.access_token'
```

### Create Performance
```bash
TOKEN="your-token-here"

curl -X POST http://localhost:8000/api/v1/performances \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Performance",
    "description": "A beautiful performance",
    "audio_file_url": null
  }' | jq '.id'
```

### Upload Audio File
```bash
TOKEN="your-token-here"
PERF_ID=1

# Create test audio (macOS/Linux)
ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 1 test.wav

# Upload it
curl -X POST http://localhost:8000/api/v1/performances/$PERF_ID/upload-audio \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.wav"
```

### Get Performance with File Info
```bash
TOKEN="your-token-here"
PERF_ID=1

curl -X GET http://localhost:8000/api/v1/performances/$PERF_ID \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.'
```

---

## Expected Test Results

Running `test_s3_local.py` should produce:

```
✓ PASS: health          (API is running)
✓ PASS: register        (User created)
✓ PASS: login           (Token received)
✓ PASS: performance_create (Performance ID created)
✓ PASS: file_upload     (File uploaded to MinIO)
✓ PASS: get_performance (File metadata stored)
✓ PASS: invalid_upload  (Invalid file rejected)
✓ PASS: large_file      (Large file rejected)

Total: 8/8 tests passed
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port already in use** | `lsof -ti:8000 \| xargs kill -9` |
| **Container won't start** | `docker compose logs backend` |
| **Database not ready** | Wait 10s, then `docker compose up` |
| **MinIO not working** | `docker compose down -v && docker compose up -d minio` |
| **API returning 500** | Check `docker compose logs backend` |
| **Can't connect to DB** | Verify `DATABASE_URL` in `.env.local` |
| **File upload fails** | Check `AWS_*` env vars and S3 bucket name |

---

## File Locations

```
project/
├── docker-compose.yml           ← Service definitions
├── .env.local                   ← Local config (copy from .env.example)
├── test_s3_local.py             ← Full test suite
├── setup_local_testing.sh       ← Setup script (macOS/Linux)
├── setup_local_testing.bat      ← Setup script (Windows)
├── LOCAL_TESTING.md             ← Detailed guide
├── backend/
│   ├── app/services/s3_storage.py  ← S3 service
│   ├── app/api/v1/performances.py  ← Upload endpoint
│   └── .env.example             ← Config template
└── terraform/
    └── DEPLOYMENT_GUIDE.md      ← AWS deployment
```

---

## Environment Variables

**In `.env.local`:**

```bash
# API
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/musician_eval

# AWS/S3 (for MinIO)
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
S3_ENDPOINT_URL=http://localhost:9000
S3_BUCKET_NAME=development-musician-eval-uploads

# Redis
REDIS_URL=redis://localhost:6379
```

---

## Common Tasks

### View All Performance Files in S3
```bash
mc ls local/development-musician-eval-uploads/performances/
```

### Download File from S3
```bash
PERF_ID=1
mc cp local/development-musician-eval-uploads/performances/$PERF_ID/ ./downloads/ --recursive
```

### Delete Test Data
```bash
docker compose exec postgres psql -U user -d musician_eval << EOF
DELETE FROM performances WHERE title LIKE 'Test%';
DELETE FROM "user" WHERE username = 'testuser';
EOF
```

### Restart Backend Only
```bash
docker compose restart backend
# or
docker compose up -d backend
```

### Stream Backend Logs
```bash
docker compose logs -f backend --tail 50
# Shows last 50 lines and follows new logs
```

### Run Tests with Verbose Output
```bash
python -u test_s3_local.py
```

---

## Next Steps

After successful local testing:

1. ✓ Test via UI at http://localhost:5173
2. ✓ Verify files in MinIO at http://localhost:9001
3. ✓ Build Docker images for ECR
4. ✓ Deploy to AWS with Terraform
5. ✓ Run staging tests

---

## Useful Links

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **MinIO Docs**: https://min.io/docs/minio/linux/index.html
- **Docker Compose Ref**: https://docs.docker.com/compose/compose-file/
- **Terraform Docs**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

---

**Questions?** Check `LOCAL_TESTING.md` for detailed guide or `AWS_S3_IMPLEMENTATION.md` for architecture details.
