# Docker & Kubernetes for Hardware Engineers

## Hardware Analogy Quick Reference

| Software | Hardware Equivalent |
|----------|---------------------|
| **Docker Image** | Firmware binary (.bin/.hex) |
| **Docker Container** | Running microcontroller |
| **docker-compose.yml** | System block diagram |
| **Port Mapping** | GPIO pin assignment |
| **Volume** | EEPROM/Flash storage |
| **Network** | I2C/SPI bus |
| **Health Check** | Watchdog timer |
| **Logs** | Serial monitor output |

---

## Docker Basics

**What is Docker?**
- **Image** = PCB design files + BOM (template)
- **Container** = Manufactured and powered board (running instance)
- **Registry** = Parts supplier (DigiKey)

**Your Project Structure:**
```
docker-compose.yml    → System integration diagram
├─ postgres          → Database (persistent storage)
├─ redis             → Cache (fast access)
└─ api               → Your FastAPI application
```

---

## Common Docker Commands

```bash
# Start all services (power on)
docker-compose up -d

# Stop all services (power off)
docker-compose down

# View logs (serial monitor)
docker-compose logs -f

# Check status (check power LEDs)
docker-compose ps

# Rebuild after code changes
docker-compose up --build

# Execute command in container (JTAG debugger)
docker exec -it <container> bash
```

---

## Kubernetes Basics

Kubernetes = **Manufacturing at scale**

| Kubernetes | Hardware Analogy |
|-----------|------------------|
| **Pod** | Single assembled PCB |
| **Deployment** | Production run (make 1000 boards) |
| **Service** | Stable test point on PCB |
| **ConfigMap** | Bill of materials (BOM) |
| **Secret** | NDA-protected schematic |

**Key Features:**
- **Health Checks** = Watchdog timers (auto-restart if frozen)
- **Replicas** = Multiple identical boards for redundancy
- **Load Balancer** = Multiplexer IC distributing requests
- **Resource Limits** = Power supply constraints (max voltage/current)

---

## Common Kubernetes Commands

```bash
# List running pods (check boards)
kubectl get pods

# View logs (serial monitor)
kubectl logs <pod-name>

# Apply configuration (deploy)
kubectl apply -f k8s/

# Check services (network endpoints)
kubectl get services

# Execute command in pod (JTAG debugger)
kubectl exec -it <pod-name> -- bash
```

---

## Your Project Architecture

```
┌──────────────┐
│  Browser     │
└──────┬───────┘
       │
┌──────▼───────┐        ┌─────────────┐
│  FastAPI     │───────→│ PostgreSQL  │ (persistent)
│  (Port 8000) │        └─────────────┘
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Redis Cache │ (fast access)
└──────────────┘
```

**Data Flow:**
1. ESP32 → POST /readings → FastAPI
2. FastAPI → Store in PostgreSQL
3. FastAPI → Cache in Redis (60% faster)
4. Dashboard → Polls every 5s → Charts update

---

## Port Mapping Explained

```yaml
ports:
  - "8000:8000"
```

**Left (8000)**: External port (your computer)
**Right (8000)**: Internal port (inside container)

**Hardware analogy:**
```
External → GPIO Expander → Internal MCU Pin
  8000         Bridge           8000
```

---

## Development vs Production

### Docker Compose (Development)
- Single machine
- Fast startup
- Easy debugging
- Like: **Breadboard prototype**

### Kubernetes (Production)
- Multiple machines
- Auto-restart on failure
- Load balancing
- Like: **Mass-manufactured PCBs**

---

## Quick Reference

### Debugging
```bash
# Check container status
docker-compose ps

# View real-time logs
docker-compose logs -f api

# Test Redis connection (expect "PONG")
docker-compose exec redis redis-cli ping

# Test PostgreSQL
docker-compose exec postgres pg_isready -U sensor_user

# Access container shell
docker-compose exec api bash
```

### Your Project
```bash
# Start everything
docker-compose up -d

# Open dashboard
http://localhost:8000

# Stop everything
docker-compose down
```

---

## Summary

**Docker** = Single device development (breadboard)
**Kubernetes** = Production deployment (mass manufacturing)

**Key Concepts:**
- Containers = Running microcontrollers
- Images = Firmware binaries
- Networks = I2C/SPI buses
- Volumes = Persistent storage (EEPROM)
- Health checks = Watchdog timers
- Logs = Serial monitor output

For more details, see [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md)
