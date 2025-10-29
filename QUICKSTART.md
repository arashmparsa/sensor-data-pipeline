# Quick Start Guide

## Start the Server

### Option 1: One Command (Easiest)
```bash
docker-compose up -d
```

### Option 2: Batch File (Windows)
Double-click `start-dashboard.bat`

### Option 3: Docker Desktop GUI
1. Open Docker Desktop
2. Navigate to project folder in terminal
3. Run: `docker-compose up -d`

Wait 15 seconds, then open: **http://localhost:8000**

---

## What You'll See

The dashboard shows:
- Real-time CO2, temperature, humidity readings
- Live updating charts (refreshes every 5 seconds)
- System status and alerts

---

## Common Commands

```bash
# Start server
docker-compose up -d

# Stop server
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Test API
curl http://localhost:8000/health
```

---

## Troubleshooting

### Port already in use?
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Can't access from another device?
Find your IP: `ipconfig`
Use: `http://YOUR_IP:8000`

### Dashboard shows "No data"?
Wait 10-15 seconds for simulator to start.

---

## Connect ESP32

Update your Arduino code with your computer's IP:
```cpp
const char* serverUrl = "http://192.168.1.100:8000/readings";
```

Find your IP: `ipconfig` (look for IPv4 Address)

---

## URLs

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
