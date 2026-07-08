@echo off
REM Local Testing Setup Script for Windows
REM Quickly sets up and runs the S3 file upload tests

setlocal enabledelayedexpansion

echo ================================
echo Musician Evaluation System
echo Local Testing Setup (Windows)
echo ================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

echo OK - Docker found

REM Check if docker compose is available
docker compose version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed
    echo Please ensure Docker Desktop is installed with Compose support
    exit /b 1
)

echo OK - Docker Compose found
echo.

REM Copy environment file
if not exist ".env.local" (
    echo Creating .env.local from template
    copy backend\.env.example .env.local >nul
    echo WARNING: Update .env.local if needed
) else (
    echo OK - .env.local already exists
)
echo.

REM Check if services are already running
docker ps --format "{{.Names}}" | findstr /c:"musician_eval_backend" >nul
if not errorlevel 1 (
    echo WARNING: Services are already running
    set /p RESTART="Do you want to restart them? (y/n): "
    if /i "!RESTART!"=="y" (
        echo Stopping existing services...
        docker compose down
    ) else (
        echo Using existing services
        goto skip_start
    )
)

REM Start services
echo Starting services (this may take a few minutes on first run)...
echo.
docker compose up -d --build

echo.
echo Waiting for services to be healthy...

REM Wait for PostgreSQL
echo   Waiting for PostgreSQL...
for /l %%i in (1,1,30) do (
    docker compose exec -T postgres pg_isready -U user >nul 2>&1
    if not errorlevel 1 (
        echo     OK - PostgreSQL ready
        goto postgres_ready
    )
    timeout /t 1 /nobreak >nul
)
:postgres_ready

REM Wait for Redis
echo   Waiting for Redis...
for /l %%i in (1,1,30) do (
    docker compose exec -T redis redis-cli ping >nul 2>&1
    if not errorlevel 1 (
        echo     OK - Redis ready
        goto redis_ready
    )
    timeout /t 1 /nobreak >nul
)
:redis_ready

REM Wait for MinIO
echo   Waiting for MinIO...
for /l %%i in (1,1,30) do (
    curl -f http://localhost:9000/minio/health/live >nul 2>&1
    if not errorlevel 1 (
        echo     OK - MinIO ready
        goto minio_ready
    )
    timeout /t 1 /nobreak >nul
)
:minio_ready

REM Wait for Backend
echo   Waiting for Backend API...
for /l %%i in (1,1,30) do (
    curl -f http://localhost:8000/api/v1/health >nul 2>&1
    if not errorlevel 1 (
        echo     OK - Backend API ready
        goto backend_ready
    )
    timeout /t 1 /nobreak >nul
)
:backend_ready

echo.
echo OK - All services are healthy
echo.

:skip_start

REM Create test audio file if it doesn't exist
if not exist "test_audio.wav" (
    echo Creating test audio file...
    python3 -c "import wave, struct; sample_rate = 44100; duration_ms = 100; num_samples = int(sample_rate * duration_ms / 1000); wav = wave.open('test_audio.wav', 'w'); wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sample_rate); wav.writeframes(struct.pack('<h', 0) * num_samples); wav.close(); print('OK - Test audio file created: test_audio.wav')"
)

echo.
echo Available Services:
echo   * Backend API: http://localhost:8000
echo   * Frontend: http://localhost:5173
echo   * MinIO Console: http://localhost:9001 ^(minioadmin/minioadmin^)
echo   * Database: localhost:5432 ^(user/password^)
echo   * Redis: localhost:6379
echo.

REM Install test dependencies
echo Installing test dependencies...
pip install -q python-dotenv requests >nul 2>&1
echo OK - Dependencies installed
echo.

REM Run the test suite
echo Running S3 File Upload Test Suite...
echo.

python3 test_s3_local.py

set TEST_EXIT_CODE=%ERRORLEVEL%

echo.
echo ================================
echo.

if %TEST_EXIT_CODE% equ 0 (
    echo SUCCESS - All tests passed!
    echo.
    echo Next steps:
    echo   1. Visit MinIO: http://localhost:9001
    echo   2. Check uploaded files in the bucket
    echo   3. Run frontend tests at http://localhost:5173
    echo   4. Review logs: docker compose logs -f backend
) else (
    echo WARNING - Some tests failed
    echo.
    echo Troubleshooting:
    echo   1. Check service logs: docker compose logs
    echo   2. Verify connectivity: curl http://localhost:8000/api/v1/health
    echo   3. Check database: docker compose exec postgres psql -U user -d musician_eval -c "SELECT 1"
    echo   4. Review LOCAL_TESTING.md for more info
)

echo ================================

exit /b %TEST_EXIT_CODE%
