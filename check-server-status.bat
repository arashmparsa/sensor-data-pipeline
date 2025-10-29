@echo off
echo ========================================
echo Sensor Data Pipeline Status
echo ========================================
echo.

echo Docker Containers:
docker-compose ps
echo.

echo Testing API Health:
curl http://localhost:8000/health
echo.

echo.
echo ========================================
echo If API is healthy, access dashboard at:
echo http://localhost:8000
echo ========================================
pause
