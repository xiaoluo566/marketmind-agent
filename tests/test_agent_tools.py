from pathlib import Path

import pytest
from app.agent.tools.builtin import (
    build_default_tool_registry,
)
from app.agent.tools.executor import ToolExecutor
from app.agent.tools.registry import ToolRegistry
from app.agent.tools.schemas import (
    ToolErrorCode,
    ToolInvocationContext,
    ToolSpec,
)
from pydantic import BaseModel


class EchoInput(BaseModel):
    message: str


class EchoOutput(BaseModel):
    reply: str


def echo_handler(payload: EchoInput, context: ToolInvocationContext) -> EchoOutput:
    return EchoOutput(reply=f"{context.trace_id}:{payload.message}")


def test_default_registry_includes_crawl_product_tool() -> None:
    registry = build_default_tool_registry()

    manifest = registry.get_manifest("crawl_product_tool")

    assert manifest.name == "crawl_product_tool"
    assert manifest.idempotent is True
    assert manifest.retryable is True
    assert manifest.input_schema == "CrawlProductToolInput"
    assert manifest.output_schema == "CrawlProductToolOutput"


def test_registry_rejects_duplicate_tool_names() -> None:
    registry = ToolRegistry()
    spec = ToolSpec(
        name="echo_tool",
        description="Echo test tool",
        input_schema=EchoInput,
        output_schema=EchoOutput,
        handler=echo_handler,
    )

    registry.register(spec)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(spec)


def test_tool_executor_returns_standardized_success_envelope_for_crawl_tool(tmp_path) -> None:
    executor = ToolExecutor(build_default_tool_registry())
    context = ToolInvocationContext(task_id="tsk_tool_001", trace_id="trc_tool_001")

    result = executor.execute(
        "crawl_product_tool",
        {
            "task_id": "tsk_tool_001",
            "url": "https://example.com/product/espresso",
            "source_type": "html_fixture",
            "html": """
                <html>
                  <body>
                    <h1>Portable Espresso Maker</h1>
                    <article class="review" data-review-id="rev-001">
                      <p>The pump stopped working after three days.</p>
                      <span>1 out of 5</span>
                    </article>
                  </body>
                </html>
            """,
            "artifact_dir": str(tmp_path),
            "save_html_artifact": True,
        },
        context=context,
    )

    assert result.success is True
    assert result.tool_name == "crawl_product_tool"
    assert result.error is None
    assert result.data is not None
    assert result.data["title"] == "Portable Espresso Maker"
    assert result.data["reviews"][0]["external_id"] == "rev-001"
    assert result.artifacts[0].artifact_type == "crawler_html"
    assert Path(result.artifacts[0].path).exists()


def test_tool_executor_returns_validation_error_for_bad_input() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolSpec(
            name="echo_tool",
            description="Echo test tool",
            input_schema=EchoInput,
            output_schema=EchoOutput,
            handler=echo_handler,
        )
    )
    executor = ToolExecutor(registry)
    context = ToolInvocationContext(task_id="tsk_tool_002", trace_id="trc_tool_002")

    result = executor.execute(
        "echo_tool",
        {"message": 123},
        context=context,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == ToolErrorCode.VALIDATION_FAILED.value


def test_tool_executor_returns_not_found_error_for_unknown_tool() -> None:
    executor = ToolExecutor(build_default_tool_registry())
    context = ToolInvocationContext(task_id="tsk_tool_003", trace_id="trc_tool_003")

    result = executor.execute(
        "missing_tool",
        {},
        context=context,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == ToolErrorCode.TOOL_NOT_FOUND.value


def test_crawl_tool_returns_classified_crawler_error(tmp_path) -> None:
    executor = ToolExecutor(build_default_tool_registry())
    context = ToolInvocationContext(task_id="tsk_tool_004", trace_id="trc_tool_004")

    result = executor.execute(
        "crawl_product_tool",
        {
            "task_id": "tsk_tool_004",
            "url": "https://example.com/product/blocked",
            "source_type": "html_fixture",
            "html": "<html><body><h1>Access Denied</h1><p>captcha</p></body></html>",
            "artifact_dir": str(tmp_path),
            "save_html_artifact": True,
        },
        context=context,
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "ACCESS_BLOCKED"
    assert result.error.details["artifacts"][0]["artifact_type"] == "crawler_failure_html"
