import os
import socket
import time
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="Load-Balanced Distributed Service",
    description="A multi-instance backend service demonstrating horizontal scaling and load balancing",
    version="1.0.0",
)

# Instance configuration from environment variables
INSTANCE_ID = os.getenv("INSTANCE_ID", socket.gethostname())
START_TIME = time.time()
_request_counter = 0


def get_and_increment_request_count() -> int:
    global _request_counter
    _request_counter += 1
    return _request_counter


class EchoRequest(BaseModel):
    message: str
    metadata: Dict[str, Any] = {}


@app.get("/", summary="Root endpoint with instance metadata")
def read_root():
    """Returns metadata about the responding backend instance and request count."""
    count = get_and_increment_request_count()
    return {
        "status": "ok",
        "message": "Distributed Multi-Instance Backend Service",
        "instance_id": INSTANCE_ID,
        "hostname": socket.gethostname(),
        "request_count": count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health", summary="Health check endpoint")
def health_check():
    """Returns instance health status used by the load balancer."""
    return {
        "status": "healthy",
        "instance_id": INSTANCE_ID,
        "uptime_seconds": round(time.time() - START_TIME, 2),
    }


@app.get("/stats", summary="Instance performance and runtime statistics")
def get_stats():
    """Returns cumulative request metrics for this instance."""
    return {
        "instance_id": INSTANCE_ID,
        "total_requests_served": _request_counter,
        "uptime_seconds": round(time.time() - START_TIME, 2),
        "hostname": socket.gethostname(),
    }


@app.post("/api/echo", summary="Echo payload with processing instance stamp")
def echo_payload(payload: EchoRequest):
    """Processes an incoming JSON payload and stamps it with the processing instance ID."""
    count = get_and_increment_request_count()
    return {
        "processed_by": INSTANCE_ID,
        "request_sequence": count,
        "echo": payload.model_dump(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not Found",
            "path": request.url.path,
            "instance_id": INSTANCE_ID,
        },
    )
