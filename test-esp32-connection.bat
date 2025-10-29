@echo off
echo ========================================
echo ESP32 Connection Diagnostics
echo ========================================
echo.

echo [1/5] Checking if API is running...
curl -s http://localhost:8000/health
if %errorlevel% equ 0 (
    echo [OK] API is running locally
) else (
    echo [FAIL] API is not responding
    goto end
)
echo.

echo [2/5] Your computer's IP addresses:
ipconfig | findstr "IPv4"
echo.

echo [3/5] Checking if port 8000 is listening...
netstat -an | findstr ":8000"
echo.

echo [4/5] Testing if API is accessible from network...
echo NOTE: If ESP32 can't reach this, check Windows Firewall!
echo.

echo [5/5] Recent API logs (looking for ESP32):
docker-compose logs --tail=20 api 2>nul | findstr /I "10.0.0"
if %errorlevel% neq 0 (
    echo No ESP32 requests found in logs yet.
    echo.
    echo DIAGNOSIS:
    echo - ESP32 may not be connected to WiFi
    echo - Windows Firewall may be blocking port 8000
    echo - ESP32 may have wrong IP address configured
)

echo.
echo ========================================
echo Troubleshooting Steps:
echo ========================================
echo.
echo 1. Check ESP32 Serial Monitor (115200 baud):
echo    - Should show "Connected to WiFi"
echo    - Should show "Upload successful!"
echo.
echo 2. Allow port 8000 in Windows Firewall:
echo    - Press Win+R, type: wf.msc
echo    - Inbound Rules ^> New Rule ^> Port ^> TCP 8000 ^> Allow
echo.
echo 3. Test from another device on same WiFi:
echo    Open browser: http://10.0.0.109:8000/health
echo.
echo 4. Check ESP32 is on same WiFi network as computer
echo.

:end
pause
