from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@patch("app.main.cache.ping", return_value=True)
def test_health_ok(mock_ping):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@patch("app.main.cache.set")
def test_create_task(mock_set):
    response = client.post("/tasks", json={"id": "101", "title": "Setup CI/CD"})
    assert response.status_code == 201
    assert response.json()["task"]["title"] == "Setup CI/CD"
