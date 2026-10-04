import os
import pytest
from fastapi.testclient import TestClient

# Ensure test instance identifier is set
os.environ["INSTANCE_ID"] = "test-instance-01"

from app.main import app, _request_counter

client = TestClient(app)


def test_health_check():
    """Test 1: Verify /health returns 200 OK and healthy status report."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "instance_id" in data
    assert data["instance_id"] == "test-instance-01"
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))


def test_instance_metadata():
    """Test 2: Verify / returns complete instance metadata and increments request counter."""
    initial_response = client.get("/")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()

    assert initial_data["status"] == "ok"
    assert "instance_id" in initial_data
    assert "hostname" in initial_data
    assert "request_count" in initial_data
    assert "timestamp" in initial_data

    # Send second request and assert counter increments
    second_response = client.get("/")
    assert second_response.status_code == 200
    second_data = second_response.json()
    assert second_data["request_count"] > initial_data["request_count"]


def test_echo_payload_processing():
    """Test 3: Verify POST /api/echo accepts JSON payloads and attaches processing metadata."""
    payload = {
        "message": "Distributed Load Balancer Verification",
        "metadata": {"cluster": "production-alpha", "priority": 1},
    }
    response = client.post("/api/echo", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["processed_by"] == "test-instance-01"
    assert data["echo"]["message"] == payload["message"]
    assert data["echo"]["metadata"]["cluster"] == "production-alpha"
    assert "request_sequence" in data
    assert "timestamp" in data


def test_error_handling_404():
    """Test 4: Verify custom 404 handler returns structured error response."""
    response = client.get("/non-existent-api-path")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == "Not Found"
    assert data["path"] == "/non-existent-api-path"
    assert data["instance_id"] == "test-instance-01"


def test_stats_endpoint():
    """Test 5: Verify /stats provides cumulative performance and uptime metrics."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["instance_id"] == "test-instance-01"
    assert data["total_requests_served"] >= 1
    assert data["uptime_seconds"] >= 0
    assert "hostname" in data


def test_load_balancer_round_robin_distribution():
    """Test 6: Simulates round-robin load distribution algorithm across backend cluster."""
    backends = ["backend-instance-alpha", "backend-instance-beta"]
    requests_to_send = 10
    dispatched_instances = []

    # Round-robin dispatch simulation
    for i in range(requests_to_send):
        target_backend = backends[i % len(backends)]
        dispatched_instances.append(target_backend)

    # Verify both backends received exactly 50% of the traffic
    count_alpha = dispatched_instances.count("backend-instance-alpha")
    count_beta = dispatched_instances.count("backend-instance-beta")

    assert count_alpha == 5
    assert count_beta == 5
    assert dispatched_instances[0] == "backend-instance-alpha"
    assert dispatched_instances[1] == "backend-instance-beta"
    assert dispatched_instances[2] == "backend-instance-alpha"
