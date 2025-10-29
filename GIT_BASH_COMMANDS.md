# Git Bash Commands

Quick reference for Git Bash (MINGW64) on Windows.

---

## Find Your IP Address

```bash
./find-my-ip.sh
```

Or manually:
```bash
ipconfig | grep -i "IPv4"
```

**Your IPs:**
- `10.0.0.109` ← WiFi connection (use this for ESP32)
- `172.24.80.1` ← Docker/virtual network (ignore)

---

## Docker Commands

```bash
# Start server
docker-compose up -d

# Stop server
docker-compose down

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up -d --build
```

---

## ESP32 Setup

1. Find your IP: `ipconfig`
2. Edit `CO2_Sensor_WiFi/CO2_Sensor_WiFi.ino`:
   ```cpp
   const char* ssid = "YourWiFiName";
   const char* password = "YourWiFiPassword";
   const char* serverUrl = "http://10.0.0.109:8000/readings";
   ```
3. Upload to ESP32 via Arduino IDE
4. Monitor: Tools > Serial Monitor (115200 baud)

---

## API Testing

```bash
# Check server health
curl http://localhost:8000/health

# Get latest reading
curl http://localhost:8000/readings/latest/ESP32_CO2_SYSTEM

# Get 24-hour history
curl http://localhost:8000/readings/history/ESP32_CO2_SYSTEM?hours=24
```

---

## Troubleshooting

### Port already in use
```bash
netstat -ano | grep :8000
taskkill /PID <PID> /F
```

### Dashboard shows no data
1. Check ESP32 Serial Monitor for "Upload successful!"
2. Verify WiFi credentials correct
3. Check server logs: `docker-compose logs -f api`

---

## URLs

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health
