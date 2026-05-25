from __future__ import annotations

from pathlib import Path

from app.crawler.artifacts import LocalCrawlerArtifactStore
from app.crawler.errors import CrawlError, CrawlErrorCode
from app.crawler.extractors import extract_product_page
from app.crawler.schemas import CrawlArtifact, CrawlRequest, CrawlResult

try:
    from playwright.async_api import Error as PlaywrightError
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright
except ImportError:  # pragma: no cover - depends on optional browser runtime install state
    async_playwright = None

    class PlaywrightError(Exception):
        pass

    class PlaywrightTimeoutError(Exception):
        pass


async def crawl_product_page(request: CrawlRequest) -> CrawlResult:
    html = await _resolve_html(request)
    try:
        result = extract_product_page(
            html=html,
            url=str(request.url),
            source_type=request.source_type,
        )
    except CrawlError as exc:
        artifacts = _save_html_artifacts(
            request=request,
            html=html,
            artifact_type="crawler_failure_html",
        )
        artifact_payload = [artifact.model_dump(mode="json") for artifact in artifacts]
        details = {**exc.details}
        if artifact_payload:
            details = {**details, "artifacts": artifact_payload}
        raise CrawlError(code=exc.code, message=str(exc), details=details) from exc

    artifacts = _save_html_artifacts(
        request=request,
        html=html,
        artifact_type="crawler_html",
    )
    if not artifacts:
        return result
    return result.model_copy(update={"artifacts": artifacts})


async def _resolve_html(request: CrawlRequest) -> str:
    if request.html is not None:
        return request.html
    if request.fixture_path is not None:
        return Path(request.fixture_path).read_text(encoding="utf-8")
    return await _fetch_html_with_playwright(request)


async def _fetch_html_with_playwright(request: CrawlRequest) -> str:
    if async_playwright is None:
        raise CrawlError(
            code=CrawlErrorCode.NETWORK_ERROR,
            message="playwright is not installed in the current environment",
            details={"url": str(request.url)},
        )

    browser = None
    try:
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context_kwargs = {}
            if request.user_agent:
                context_kwargs["user_agent"] = request.user_agent
            context = await browser.new_context(**context_kwargs)
            page = await context.new_page()
            await page.goto(
                str(request.url),
                wait_until="domcontentloaded",
                timeout=request.timeout_ms,
            )
            try:
                await page.wait_for_load_state("networkidle", timeout=request.timeout_ms)
            except PlaywrightTimeoutError:
                pass
            return await page.content()
    except PlaywrightTimeoutError as exc:
        raise CrawlError(
            code=CrawlErrorCode.PAGE_TIMEOUT,
            message="page loading timed out",
            details={"url": str(request.url), "timeout_ms": request.timeout_ms},
        ) from exc
    except PlaywrightError as exc:
        raise CrawlError(
            code=CrawlErrorCode.NETWORK_ERROR,
            message="playwright failed to load page",
            details={"url": str(request.url), "reason": str(exc)},
        ) from exc
    finally:
        if browser is not None:
            await browser.close()


def _save_html_artifacts(
    *,
    request: CrawlRequest,
    html: str,
    artifact_type: str,
) -> list[CrawlArtifact]:
    if not request.save_html_artifact or request.artifact_dir is None or request.task_id is None:
        return []

    store = LocalCrawlerArtifactStore(request.artifact_dir)
    saved = store.save_text(
        task_id=request.task_id,
        artifact_type=artifact_type,
        content=html,
        extension="html",
        mime_type="text/html",
    )
    return [saved.artifact]
