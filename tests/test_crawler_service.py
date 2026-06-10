import asyncio
from pathlib import Path

from app.crawler.errors import CrawlError, CrawlErrorCode
from app.crawler.schemas import CrawlRequest
from app.crawler.service import crawl_product_page


def test_crawl_product_page_extracts_fixture_content() -> None:
    request = CrawlRequest(
        url="https://example.com/product/espresso",
        source_type="html_fixture",
        html="""
            <html>
              <head><title>Portable Espresso Maker</title></head>
              <body>
                <h1>Portable Espresso Maker</h1>
                <p>Best for travel.</p>
                <div>Only $39.99 today.</div>
                <div>4.6 out of 5 stars</div>
              </body>
            </html>
        """,
    )

    result = asyncio.run(crawl_product_page(request))

    assert result.title == "Portable Espresso Maker"
    assert result.price == 39.99
    assert result.rating == 4.6
    assert "Best for travel." in result.extracted_text
    assert result.source_type == "html_fixture"


def test_crawl_product_page_extracts_structured_reviews() -> None:
    request = CrawlRequest(
        url="https://example.com/product/espresso",
        source_type="html_fixture",
        html="""
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
    )

    result = asyncio.run(crawl_product_page(request))

    assert len(result.reviews) == 1
    assert result.reviews[0].external_id == "rev-001"
    assert "pump stopped working" in result.reviews[0].content
    assert result.reviews[0].rating == 1.0


def test_crawl_product_page_extracts_low_risk_json_ld_reviews() -> None:
    request = CrawlRequest(
        url="https://shop.example/products/desk-lamp",
        source_type="html_fixture",
        html="""
            <html>
              <head>
                <script type="application/ld+json">
                  {
                    "@type": "Product",
                    "name": "Adjustable Desk Lamp",
                    "review": [
                      {
                        "@type": "Review",
                        "author": {"name": "buyer-a"},
                        "reviewRating": {"ratingValue": "1"},
                        "reviewBody": "The hinge loosened after two days.",
                        "url": "https://shop.example/products/desk-lamp#review-1"
                      },
                      {
                        "@type": "Review",
                        "author": "buyer-b",
                        "reviewRating": {"ratingValue": 2},
                        "reviewBody": "Shipping was slow and support never replied."
                      }
                    ]
                  }
                </script>
              </head>
              <body>
                <h1>Adjustable Desk Lamp</h1>
                <p>$29.99</p>
              </body>
            </html>
        """,
    )

    result = asyncio.run(crawl_product_page(request))

    assert result.title == "Adjustable Desk Lamp"
    assert len(result.reviews) == 2
    assert result.reviews[0].content == "The hinge loosened after two days."
    assert result.reviews[0].rating == 1.0
    assert result.reviews[0].source_url == "https://shop.example/products/desk-lamp#review-1"
    assert result.reviews[0].metadata["extractor"] == "json_ld_product_review"
    assert result.metadata["extractor"] == "json_ld_product"


def test_crawl_product_page_rejects_blocked_pages() -> None:
    request = CrawlRequest(
        url="https://example.com/product/blocked",
        source_type="html_fixture",
        html="""
            <html>
              <body>
                <h1>Access Denied</h1>
                <p>Please verify you are human.</p>
              </body>
            </html>
        """,
    )

    try:
        asyncio.run(crawl_product_page(request))
    except CrawlError as exc:
        assert exc.code == CrawlErrorCode.ACCESS_BLOCKED
    else:  # pragma: no cover - defensive branch
        raise AssertionError("expected access blocked error")


def test_crawl_product_page_requires_visible_content() -> None:
    request = CrawlRequest(
        url="https://example.com/product/empty",
        source_type="html_fixture",
        html="<html><body><script>window.a = 1</script></body></html>",
    )

    try:
        asyncio.run(crawl_product_page(request))
    except CrawlError as exc:
        assert exc.code == CrawlErrorCode.DOM_NOT_FOUND
    else:  # pragma: no cover - defensive branch
        raise AssertionError("expected dom not found error")


def test_crawl_product_page_saves_success_html_artifact(tmp_path) -> None:
    request = CrawlRequest(
        task_id="tsk_crawl_artifact",
        url="https://example.com/product/espresso",
        source_type="html_fixture",
        html="<html><body><h1>Portable Espresso Maker</h1><p>$39.99</p></body></html>",
        artifact_dir=str(tmp_path),
        save_html_artifact=True,
    )

    result = asyncio.run(crawl_product_page(request))

    assert len(result.artifacts) == 1
    artifact = result.artifacts[0]
    assert artifact.artifact_type == "crawler_html"
    assert artifact.mime_type == "text/html"
    assert artifact.checksum is not None
    assert Path(artifact.path).exists()
    assert "Portable Espresso Maker" in Path(artifact.path).read_text(encoding="utf-8")


def test_crawl_product_page_attaches_failure_artifact(tmp_path) -> None:
    request = CrawlRequest(
        task_id="tsk_crawl_failure_artifact",
        url="https://example.com/product/blocked",
        source_type="html_fixture",
        html="<html><body><h1>Access Denied</h1><p>captcha</p></body></html>",
        artifact_dir=str(tmp_path),
        save_html_artifact=True,
    )

    try:
        asyncio.run(crawl_product_page(request))
    except CrawlError as exc:
        assert exc.code == CrawlErrorCode.ACCESS_BLOCKED
        assert exc.details["artifacts"][0]["artifact_type"] == "crawler_failure_html"
    else:  # pragma: no cover - defensive branch
        raise AssertionError("expected access blocked error")
