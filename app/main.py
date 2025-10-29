from fastapi import FastAPI, Depends, BackgroundTasks, Body
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
import redis
import json
from typing import List, Optional
import os
from pathlib import Path

from .database import SessionLocal, SensorReading
from .sensor_simulator import SensorSimulator

# Pydantic model for sensor reading
class SensorReadingInput(BaseModel):
    sensor_id: str
    co2_ppm: float
    temperature: float
    humidity: float

app = FastAPI(title="IoT Sensor Data Pipeline")

# Serve dashboard HTML
templates_dir = Path(__file__).parent / "templates"

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

@app.get("/", response_class=HTMLResponse)
def read_root():
    '''Serve the dashboard GUI with no-cache headers'''
    from fastapi.responses import Response
    dashboard_path = templates_dir / "dashboard.html"
    if dashboard_path.exists():
        content = dashboard_path.read_text()
        return Response(
            content=content,
            media_type="text/html",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"status": "IoT Sensor Pipeline Active", "version": "1.0.0"}

@app.get("/health")
def health_check():
    '''API health check endpoint'''
    return {"status": "IoT Sensor Pipeline Active", "version": "1.0.0"}

@app.post("/readings")
def create_reading(
    reading: SensorReadingInput,
    db: Session = Depends(get_db)
):
    '''Receive sensor reading from ESP32 or other sensors and store in DB + Redis'''

    # Build reading data from POST body
    reading_data = {
        "sensor_id": reading.sensor_id,
        "co2_ppm": reading.co2_ppm,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Store in PostgreSQL
    db_reading = SensorReading(
        sensor_id=reading.sensor_id,
        co2_ppm=reading.co2_ppm,
        temperature=reading.temperature,
        humidity=reading.humidity
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    # Cache latest reading in Redis
    redis_client.setex(
        f"sensor:{reading.sensor_id}:latest",
        300,  # 5 min TTL
        json.dumps(reading_data)
    )

    print(f"✅ Received from {reading.sensor_id}: CO2={reading.co2_ppm:.1f} ppm, Temp={reading.temperature:.1f}C, Humidity={reading.humidity:.1f}%")

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
    '''Startup event - simulator enabled for testing'''
    print("🚀 IoT Sensor API Started - Ready to receive ESP32 data!")
    print("📡 Listening for POST requests at /readings")
    print("🔍 Check dashboard at http://localhost:8000")
    print("⚠️  Simulator enabled - generating test data every 10s")

    # Simulator enabled - generating test data
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
