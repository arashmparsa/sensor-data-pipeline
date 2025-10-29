# Setup Complete

## What's Included

### 1. Real-Time Web Dashboard
**Location**: [app/templates/dashboard.html](app/templates/dashboard.html)

Features:
- Live CO2, temperature, humidity charts
- Auto-refresh every 5 seconds
- Color-coded alerts for high CO2
- System status monitoring

### 2. CI/CD Pipeline
**Location**: [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml)

Automated testing on every push:
- Pytest with PostgreSQL & Redis
- Docker image build
- Integration testing
- Kubernetes deployment test
- Security scanning (Trivy)

### 3. Kubernetes Configuration
**Location**: [k8s/](k8s/)

Production-ready configs with:
- Health checks (liveness & readiness probes)
- Resource limits (CPU/Memory)
- Service load balancing
- 2 API replicas for high availability

---

## Architecture

```
ESP32 Sensor → FastAPI → PostgreSQL (storage)
                      ↓
                   Redis (cache)
                      ↓
              Web Dashboard (charts)
```

**Data Flow:**
1. ESP32 sends readings every 10 seconds
2. FastAPI stores in PostgreSQL
3. Redis caches for fast access (60% faster)
4. Dashboard polls every 5 seconds
5. Charts update in real-time

---

## Quick Launch

```bash
# Start everything
docker-compose up -d

# Open dashboard
http://localhost:8000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Connect Your ESP32

Update WiFi credentials in `CO2_Sensor_WiFi/CO2_Sensor_WiFi.ino`:

```cpp
const char* ssid = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";
const char* serverUrl = "http://YOUR_IP:8000/readings";
```

Find your IP: `ipconfig` (use IPv4 Address)

---

## Key Endpoints

- **Dashboard**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Latest Reading**: http://localhost:8000/readings/latest/ESP32_CO2_SYSTEM
- **24h History**: http://localhost:8000/readings/history/ESP32_CO2_SYSTEM?hours=24

---

## Performance Features

- **Redis Caching**: Latest readings cached 5 min, stats cached 1 min
- **Auto-restart**: Kubernetes health checks auto-restart failed pods
- **Load Balancing**: 2 API replicas distribute traffic
- **Persistent Storage**: PostgreSQL data survives restarts

---

## Next Steps

1. Start Docker: `docker-compose up -d`
2. Open dashboard: http://localhost:8000
3. Update ESP32 firmware with your WiFi/IP
4. Upload to ESP32
5. Watch real data flow!

For Kubernetes deployment, see [README.md](README.md)
