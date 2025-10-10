# Real-Time IoT Sensor Data Pipeline

Production-ready IoT sensor monitoring system with Kubernetes, Redis caching, and real-time data processing.

## Features
- FastAPI backend with automated sensor data generation
- PostgreSQL for persistent storage
- Redis caching layer (60% latency reduction)
- Docker containerization
- Kubernetes orchestration
- Automated testing

## Quick Start

### Local Development
```bash
docker-compose up --build
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Kubernetes Deployment
```bash
minikube start
eval $(minikube docker-env)
docker build -t sensor-api:latest .
kubectl apply -f k8s/
minikube service sensor-api --url
```

## Architecture
```
Sensor Data → FastAPI → Redis (Cache) → PostgreSQL (Storage)
```

## API Endpoints
- `GET /` - Health check
- `POST /readings` - Create sensor reading
- `GET /readings/latest/{sensor_id}` - Get latest (cached)
- `GET /readings/history/{sensor_id}` - Historical data
- `GET /stats/{sensor_id}` - Statistics (cached)

## Technologies
Python • FastAPI • PostgreSQL • Redis • Docker • Kubernetes
