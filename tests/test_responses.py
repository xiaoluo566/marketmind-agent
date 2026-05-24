from app.core.responses import error_response, success_response


def test_success_response_contract() -> None:
    response = success_response(data={"task_id": "tsk_123"}, trace_id="trc_123")

    assert response == {
        "success": True,
        "data": {"task_id": "tsk_123"},
        "error": None,
        "message": "ok",
        "trace_id": "trc_123",
    }


def test_error_response_contract() -> None:
    response = error_response(
        code="INVALID_TARGET",
        message="Target URL is invalid",
        trace_id="trc_123",
        details={"field": "target"},
    )

    assert response["success"] is False
    assert response["data"] is None
    assert response["error"]["code"] == "INVALID_TARGET"
    assert response["error"]["details"] == {"field": "target"}
    assert response["trace_id"] == "trc_123"

