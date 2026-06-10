from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from typing import Any

from app.crawler.errors import CrawlError, CrawlErrorCode
from app.crawler.schemas import CrawlResult, CrawlReview

_BLOCKED_MARKERS = (
    "access denied",
    "captcha",
    "verify you are human",
    "unusual traffic",
)


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: str | None = None
        self.heading: str | None = None
        self._active_tag: str | None = None
        self._skip_depth = 0
        self._text_parts: list[str] = []
        self._review_depth = 0
        self._review_external_id: str | None = None
        self._review_parts: list[str] = []
        self._json_ld_depth = 0
        self._json_ld_parts: list[str] = []
        self.reviews: list[CrawlReview] = []
        self.json_ld_documents: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        normalized_tag = tag.lower()
        attrs_dict = {name.lower(): value for name, value in attrs}
        if normalized_tag == "script" and _is_json_ld_script(attrs_dict):
            self._json_ld_depth = 1
        if normalized_tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if normalized_tag in {"title", "h1"}:
            self._active_tag = normalized_tag
        if self._is_review_container(normalized_tag, attrs_dict):
            self._review_depth = 1
            self._review_external_id = (
                attrs_dict.get("data-review-id")
                or attrs_dict.get("data-review")
                or attrs_dict.get("id")
            )
            self._review_parts = []
        elif self._review_depth:
            self._review_depth += 1

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if self._json_ld_depth:
            self._json_ld_depth -= 1
            if self._json_ld_depth == 0 and self._json_ld_parts:
                self.json_ld_documents.append("\n".join(self._json_ld_parts))
                self._json_ld_parts = []
        if self._active_tag == normalized_tag:
            self._active_tag = None
        if self._review_depth:
            self._review_depth -= 1
            if self._review_depth == 0:
                self._append_review()

    def handle_data(self, data: str) -> None:
        if self._json_ld_depth:
            self._json_ld_parts.append(data)
            return
        if self._skip_depth:
            return
        value = normalize_text(data)
        if not value:
            return
        self._text_parts.append(value)
        if self._review_depth:
            self._review_parts.append(value)
        if self._active_tag == "title" and self.title is None:
            self.title = value
        if self._active_tag == "h1" and self.heading is None:
            self.heading = value

    def visible_text(self) -> str:
        return normalize_text(" ".join(self._text_parts))

    def _append_review(self) -> None:
        content = normalize_text(" ".join(self._review_parts))
        if not content:
            return
        self.reviews.append(
            CrawlReview(
                external_id=self._review_external_id,
                content=content,
                rating=_extract_rating(content),
                metadata={"extractor": "generic_html_review"},
            )
        )
        self._review_external_id = None
        self._review_parts = []

    def _is_review_container(self, tag: str, attrs: dict[str, str | None]) -> bool:
        if tag not in {"article", "div", "li", "section"}:
            return False
        class_value = attrs.get("class") or ""
        itemprop_value = attrs.get("itemprop") or ""
        return (
            "review" in class_value.lower()
            or itemprop_value.lower() == "review"
            or attrs.get("data-review-id") is not None
            or attrs.get("data-review") is not None
        )


def extract_product_page(html: str, url: str, source_type: str) -> CrawlResult:
    parser = _VisibleTextParser()
    try:
        parser.feed(html)
    except Exception as exc:
        raise CrawlError(
            code=CrawlErrorCode.PARSER_ERROR,
            message="failed to parse page html",
            details={"reason": str(exc)},
        ) from exc

    text = parser.visible_text()
    if _looks_blocked(text):
        raise CrawlError(
            code=CrawlErrorCode.ACCESS_BLOCKED,
            message="page appears to be blocked by access controls",
            details={"url": url},
        )

    json_ld_product = _extract_json_ld_product(parser.json_ld_documents)
    title = parser.heading or parser.title or json_ld_product.get("title")
    if title is None or not text:
        raise CrawlError(
            code=CrawlErrorCode.DOM_NOT_FOUND,
            message="page does not contain enough visible product content",
            details={"url": url},
        )

    json_ld_reviews = json_ld_product.get("reviews")
    reviews = [*parser.reviews, *(json_ld_reviews if isinstance(json_ld_reviews, list) else [])]
    return CrawlResult(
        url=url,
        source_type=source_type,
        title=title,
        price=_extract_price(text),
        rating=_extract_rating(text),
        extracted_text=text,
        html=html,
        reviews=reviews,
        metadata={"extractor": "json_ld_product" if json_ld_reviews else "generic_html"},
    )


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(value)).strip()


def _extract_price(text: str) -> float | None:
    match = re.search(r"(?:US\$|\$)\s*([0-9]+(?:\.[0-9]{1,2})?)", text)
    if match is None:
        return None
    return float(match.group(1))


def _extract_rating(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:\.[0-9])?)\s*(?:/5|out of 5)", text, flags=re.I)
    if match is None:
        return None
    return float(match.group(1))


def _looks_blocked(text: str) -> bool:
    lower_text = text.lower()
    return any(marker in lower_text for marker in _BLOCKED_MARKERS)


def _is_json_ld_script(attrs: dict[str, str | None]) -> bool:
    script_type = attrs.get("type") or ""
    return script_type.lower().strip() == "application/ld+json"


def _extract_json_ld_product(documents: list[str]) -> dict[str, Any]:
    for document in documents:
        try:
            decoded = json.loads(document)
        except json.JSONDecodeError:
            continue
        product = _find_json_ld_product(decoded)
        if product is None:
            continue
        return {
            "title": _json_text(product.get("name")),
            "reviews": _json_ld_reviews(product),
        }
    return {}


def _find_json_ld_product(value: Any) -> dict[str, Any] | None:
    if isinstance(value, list):
        for item in value:
            product = _find_json_ld_product(item)
            if product is not None:
                return product
        return None
    if not isinstance(value, dict):
        return None

    if _matches_json_ld_type(value.get("@type"), "Product"):
        return value
    graph = value.get("@graph")
    if isinstance(graph, list):
        return _find_json_ld_product(graph)
    return None


def _json_ld_reviews(product: dict[str, Any]) -> list[CrawlReview]:
    raw_reviews = product.get("review") or product.get("reviews") or []
    if isinstance(raw_reviews, dict):
        raw_reviews = [raw_reviews]
    if not isinstance(raw_reviews, list):
        return []

    reviews: list[CrawlReview] = []
    for index, raw_review in enumerate(raw_reviews, start=1):
        if not isinstance(raw_review, dict):
            continue
        content = normalize_text(
            _json_text(raw_review.get("reviewBody") or raw_review.get("description")) or ""
        )
        if not content:
            continue
        reviews.append(
            CrawlReview(
                external_id=_json_text(raw_review.get("@id") or raw_review.get("id"))
                or f"jsonld-review-{index}",
                content=content,
                rating=_json_ld_rating(raw_review.get("reviewRating")),
                source_url=_json_text(raw_review.get("url")),
                metadata={
                    "extractor": "json_ld_product_review",
                    "author": _json_ld_author(raw_review.get("author")),
                },
            )
        )
    return reviews


def _json_ld_rating(value: Any) -> float | None:
    if isinstance(value, dict):
        value = value.get("ratingValue") or value.get("rating")
    text_value = _json_text(value)
    if text_value is None:
        return None
    try:
        return float(text_value)
    except ValueError:
        return None


def _json_ld_author(value: Any) -> str | None:
    if isinstance(value, dict):
        return _json_text(value.get("name"))
    return _json_text(value)


def _matches_json_ld_type(value: Any, expected: str) -> bool:
    if isinstance(value, list):
        return any(_matches_json_ld_type(item, expected) for item in value)
    return isinstance(value, str) and value.lower() == expected.lower()


def _json_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
