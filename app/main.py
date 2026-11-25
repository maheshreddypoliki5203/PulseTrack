import os
import redis
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="PulseTrack API")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
APP_ENV = os.getenv("APP_ENV", "dev")

cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

REQUEST_COUNT = Counter(
    "pulsetrack_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

class Task(BaseModel):
    id: str
    title: str

@app.get("/health")
def health_check():
    try:
        cache.ping()
        REQUEST_COUNT.labels("GET", "/health", "200").inc()
        return {"status": "healthy", "environment": APP_ENV, "redis": "connected"}
    except redis.ConnectionError:
        REQUEST_COUNT.labels("GET", "/health", "503").inc()
        raise HTTPException(status_code=503, detail="Redis unavailable")

@app.post("/tasks", status_code=201)
def create_task(task: Task):
    cache.set(f"task:{task.id}", task.title)
    REQUEST_COUNT.labels("POST", "/tasks", "201").inc()
    return {"message": "Task saved", "task": task}

@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    title = cache.get(f"task:{task_id}")
    if not title:
        REQUEST_COUNT.labels("GET", "/tasks", "404").inc()
        raise HTTPException(status_code=404, detail="Task not found")
    REQUEST_COUNT.labels("GET", "/tasks", "200").inc()
    return {"id": task_id, "title": title}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
