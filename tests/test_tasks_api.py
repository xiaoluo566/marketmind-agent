from app.main import create_app
from fastapi.testclient import TestClient


def test_create_task_returns_accepted_envelope() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_day4_task"},
        json={
            "target": "https://example.com/products/portable-espresso-maker",
            "mode": "competitive_research",
            "priority": "normal",
            "source_type": "public_url",
            "options": {
                "use_rag": True,
                "export_format": "markdown",
            },
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["success"] is True
    assert body["error"] is None
    assert body["message"] == "accepted"
    assert body["trace_id"] == "trc_day4_task"
    assert response.headers["X-Trace-Id"] == "trc_day4_task"
    assert body["data"]["task_id"].startswith("tsk_")
    assert body["data"]["status"] == "received"
    assert body["data"]["trace_id"] == "trc_day4_task"


def test_create_task_applies_contract_defaults() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/tasks",
        json={"target": "demo://portable-espresso-maker-negative-reviews"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["data"]["status"] == "received"
    assert body["trace_id"].startswith("trc_")


def test_create_task_validation_error_uses_api_envelope() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/tasks",
        headers={"X-Trace-Id": "trc_invalid_task"},
        json={
            "target": "   ",
            "mode": "unsupported_mode",
            "priority": "urgent",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"] == "request validation failed"
    assert body["trace_id"] == "trc_invalid_task"
    assert response.headers["X-Trace-Id"] == "trc_invalid_task"
    assert body["error"]["code"] == "VALIDATION_FAILED"
    assert body["error"]["details"]["errors"]
