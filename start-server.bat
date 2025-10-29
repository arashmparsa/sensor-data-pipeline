@echo off
echo ========================================
echo Starting Sensor Data Pipeline Server
echo ========================================
echo.

echo Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running!
echo.
echo Starting PostgreSQL, Redis, and FastAPI...
docker-compose up -d

echo.
echo ========================================
echo Server Status:
echo ========================================
docker-compose ps

echo.
echo ========================================
echo Access the dashboard at:
echo http://localhost:8000
echo ========================================
echo.
echo Server is running in background.
echo To stop: run stop-server.bat
pause
