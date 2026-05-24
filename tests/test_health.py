from app.main import create_app
from fastapi.testclient import TestClient


def test_health_returns_api_envelope() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "ok"
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "MarketMind Agent API"
    assert body["trace_id"].startswith("trc_")
    assert response.headers["X-Trace-Id"] == body["trace_id"]


def test_health_preserves_inbound_trace_id() -> None:
    client = TestClient(create_app())

    response = client.get("/api/health", headers={"X-Trace-Id": "trc_test_123"})

    assert response.status_code == 200
    body = response.json()
    assert body["trace_id"] == "trc_test_123"
    assert response.headers["X-Trace-Id"] == "trc_test_123"

