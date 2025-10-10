import pytest
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
