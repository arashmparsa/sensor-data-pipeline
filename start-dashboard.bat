@echo off
echo ========================================
echo IoT Sensor Dashboard - Quick Start
echo ========================================
echo.
echo Starting services (API, PostgreSQL, Redis)...
echo.

docker-compose up --build -d

echo.
echo Waiting for services to initialize (15 seconds)...
timeout /t 15 /nobreak > nul

echo.
echo ========================================
echo Dashboard is ready!
echo ========================================
echo.
echo Open in your browser:
echo   Dashboard:  http://localhost:8000
echo   API Docs:   http://localhost:8000/docs
echo   Health:     http://localhost:8000/health
echo.
echo To view logs: docker-compose logs -f api
echo To stop:      docker-compose down
echo.

start http://localhost:8000

echo Press any key to view logs...
pause > nul
docker-compose logs -f api
