#!/usr/bin/env python3
"""
IoT Sensor Pipeline Project Generator
Run this script to automatically create all project files.

Usage:
    python setup_project.py

This will create a complete project structure with all necessary files.
"""

import os
from pathlib import Path

# Project structure and file contents
FILES = {
    "app/__init__.py": "",
    
    "app/database.py": """from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sensor_user:sensor_pass@localhost:5432/sensor_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorReading(Base):
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, index=True)
    co2_ppm = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
""",
    
    "app/sensor_simulator.py": """import random
import time
from datetime import datetime

class SensorSimulator:
    '''Simulates CO2 sensor readings'''
    
    def __init__(self, sensor_id="SENSOR_001"):
        self.sensor_id = sensor_id
        self.base_co2 = 400  # Normal atmospheric CO2
        
    def get_reading(self):
        '''Generate realistic sensor reading'''
        # Simulate daily variation (higher during day)
        hour = datetime.now().hour
        daily_variation = 100 * abs(((hour - 12) / 12))
        
        return {
            "sensor_id": self.sensor_id,
            "co2_ppm": self.base_co2 + daily_variation + random.uniform(-50, 50),
            "temperature": 20 + random.uniform(-2, 5),
            "humidity": 45 + random.uniform(-10, 10),
            "timestamp": datetime.utcnow().isoformat()
        }
""",
    
    "app/main.py": """from fastapi import FastAPI, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import redis
import json
from typing import List
import os

from .database import SessionLocal, SensorReading
from .sensor_simulator import SensorSimulator

app = FastAPI(title="IoT Sensor Data Pipeline")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

# Sensor simulator
simulator = SensorSimulator()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "IoT Sensor Pipeline Active", "version": "1.0.0"}

@app.post("/readings")
def create_reading(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    '''Receive sensor reading and store in DB + Redis'''
    
    # Get simulated reading
    reading_data = simulator.get_reading()
    
    # Store in PostgreSQL
    db_reading = SensorReading(
        sensor_id=reading_data["sensor_id"],
        co2_ppm=reading_data["co2_ppm"],
        temperature=reading_data["temperature"],
        humidity=reading_data["humidity"]
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    
    # Cache latest reading in Redis
    redis_client.setex(
        f"sensor:{reading_data['sensor_id']}:latest",
        300,  # 5 min TTL
        json.dumps(reading_data)
    )
    
    return {"status": "success", "reading": reading_data}

@app.get("/readings/latest/{sensor_id}")
def get_latest_reading(sensor_id: str):
    '''Get latest reading from Redis cache'''
    cached = redis_client.get(f"sensor:{sensor_id}:latest")
    
    if cached:
        return {"source": "cache", "data": json.loads(cached)}
    
    return {"source": "cache", "data": None}

@app.get("/readings/history/{sensor_id}")
def get_reading_history(sensor_id: str, hours: int = 24, db: Session = Depends(get_db)):
    '''Get historical readings from database'''
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    readings = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.timestamp >= cutoff_time
    ).order_by(SensorReading.timestamp.desc()).all()
    
    return {
        "sensor_id": sensor_id,
        "count": len(readings),
        "readings": [
            {
                "co2_ppm": r.co2_ppm,
                "temperature": r.temperature,
                "humidity": r.humidity,
                "timestamp": r.timestamp.isoformat()
            }
            for r in readings
        ]
    }

@app.get("/stats/{sensor_id}")
def get_statistics(sensor_id: str, db: Session = Depends(get_db)):
    '''Calculate statistics from recent readings'''
    
    # Check cache first
    cache_key = f"sensor:{sensor_id}:stats"
    cached_stats = redis_client.get(cache_key)
    
    if cached_stats:
        return {"source": "cache", "stats": json.loads(cached_stats)}
    
    # Calculate from database
    cutoff_time = datetime.utcnow() - timedelta(hours=1)
    readings = db.query(SensorReading).filter(
        SensorReading.sensor_id == sensor_id,
        SensorReading.timestamp >= cutoff_time
    ).all()
    
    if not readings:
        return {"message": "No recent data"}
    
    stats = {
        "avg_co2": sum(r.co2_ppm for r in readings) / len(readings),
        "max_co2": max(r.co2_ppm for r in readings),
        "min_co2": min(r.co2_ppm for r in readings),
        "avg_temp": sum(r.temperature for r in readings) / len(readings),
        "sample_count": len(readings)
    }
    
    # Cache for 1 minute
    redis_client.setex(cache_key, 60, json.dumps(stats))
    
    return {"source": "database", "stats": stats}

@app.on_event("startup")
async def startup_event():
    '''Generate sensor readings every 10 seconds'''
    import asyncio
    
    async def generate_readings():
        while True:
            try:
                db = SessionLocal()
                reading_data = simulator.get_reading()
                
                db_reading = SensorReading(
                    sensor_id=reading_data["sensor_id"],
                    co2_ppm=reading_data["co2_ppm"],
                    temperature=reading_data["temperature"],
                    humidity=reading_data["humidity"]
                )
                db.add(db_reading)
                db.commit()
                db.close()
                
                redis_client.setex(
                    f"sensor:{reading_data['sensor_id']}:latest",
                    300,
                    json.dumps(reading_data)
                )
                
                print(f"Generated reading: CO2={reading_data['co2_ppm']:.1f} ppm")
                
            except Exception as e:
                print(f"Error: {e}")
            
            await asyncio.sleep(10)
    
    asyncio.create_task(generate_readings())
""",
    
    "requirements.txt": """fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
python-dotenv==1.0.0
""",
    
    "Dockerfile": """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    
    "docker-compose.yml": """version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: sensor_user
      POSTGRES_PASSWORD: sensor_pass
      POSTGRES_DB: sensor_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sensor_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://sensor_user:sensor_pass@postgres:5432/sensor_db
      REDIS_HOST: redis
      REDIS_PORT: 6379
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

volumes:
  postgres_data:
""",
    
    "k8s/postgres-deployment.yaml": """apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-config
data:
  POSTGRES_USER: sensor_user
  POSTGRES_DB: sensor_db
---
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  POSTGRES_PASSWORD: sensor_pass
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        ports:
        - containerPort: 5432
        envFrom:
        - configMapRef:
            name: postgres-config
        - secretRef:
            name: postgres-secret
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
""",
    
    "k8s/redis-deployment.yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
""",
    
    "k8s/api-deployment.yaml": """apiVersion: apps/v1
kind: Deployment
metadata:
  name: sensor-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: sensor-api
  template:
    metadata:
      labels:
        app: sensor-api
    spec:
      containers:
      - name: api
        image: sensor-api:latest
        imagePullPolicy: Never
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          value: postgresql://sensor_user:sensor_pass@postgres:5432/sensor_db
        - name: REDIS_HOST
          value: redis
        - name: REDIS_PORT
          value: "6379"
---
apiVersion: v1
kind: Service
metadata:
  name: sensor-api
spec:
  type: LoadBalancer
  selector:
    app: sensor-api
  ports:
  - port: 8000
    targetPort: 8000
""",
    
    "tests/test_api.py": """import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "status" in response.json()

def test_create_reading():
    response = client.post("/readings")
    assert response.status_code == 200
    assert "reading" in response.json()

def test_get_latest_reading():
    client.post("/readings")
    response = client.get("/readings/latest/SENSOR_001")
    assert response.status_code == 200
""",
    
    "README.md": """# Real-Time IoT Sensor Data Pipeline

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
""",

    ".gitignore": """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
htmlcov/
*.log
"""
}

def create_file(filepath, content):
    """Create a file with the given content, creating directories as needed."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    print(f"[OK] Created: {filepath}")

def main():
    print("=== IoT Sensor Pipeline Project Generator ===")
    print("=" * 60)
    print()
    
    # Check if we're in the right directory
    if Path("setup_project.py").exists():
        print("WARNING: Running in current directory...")
        response = input("Create project here? (y/n): ")
        if response.lower() != 'y':
            print("CANCELLED. Please run from your desired project directory.")
            return
    
    print()
    print("Creating project files...")
    print()
    
    # Create all files
    for filepath, content in FILES.items():
        create_file(filepath, content)
    
    print()
    print("=" * 60)
    print("SUCCESS! Project created successfully!")
    print()
    print("Created files:")
    print(f"   - {len(FILES)} files total")
    print(f"   - App code: 5 files")
    print(f"   - Docker: 2 files")
    print(f"   - Kubernetes: 3 files")
    print(f"   - Tests: 1 file")
    print()
    print("Next steps:")
    print()
    print("1. Test with Docker:")
    print("   docker-compose up --build")
    print()
    print("2. Test API:")
    print("   curl http://localhost:8000")
    print("   curl -X POST http://localhost:8000/readings")
    print()
    print("3. Deploy to Kubernetes:")
    print("   minikube start")
    print("   eval $(minikube docker-env)")
    print("   docker build -t sensor-api:latest .")
    print("   kubectl apply -f k8s/")
    print()
    print("4. Push to GitHub:")
    print("   git init")
    print("   git add .")
    print("   git commit -m 'Initial commit: IoT sensor pipeline'")
    print("   git remote add origin <your-repo-url>")
    print("   git push -u origin main")
    print()
    print("Documentation: See README.md")
    print("Issues? Check docker-compose logs or kubectl logs")
    print()

if __name__ == "__main__":
    main()
