@echo off
echo ========================================
echo Finding Your Laptop's IP Address
echo ========================================
echo.

ipconfig | findstr /i "IPv4"

echo.
echo ========================================
echo Use one of the IP addresses above in your ESP32 firmware:
echo const char* serverUrl = "http://YOUR_IP:8000/readings";
echo ========================================
pause
