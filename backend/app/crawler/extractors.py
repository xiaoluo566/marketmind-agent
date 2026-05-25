from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

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
        self.reviews: list[CrawlReview] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        normalized_tag = tag.lower()
        attrs_dict = {name.lower(): value for name, value in attrs}
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
        if self._active_tag == normalized_tag:
            self._active_tag = None
        if self._review_depth:
            self._review_depth -= 1
            if self._review_depth == 0:
                self._append_review()

    def handle_data(self, data: str) -> None:
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

    title = parser.heading or parser.title
    if title is None or not text:
        raise CrawlError(
            code=CrawlErrorCode.DOM_NOT_FOUND,
            message="page does not contain enough visible product content",
            details={"url": url},
        )

    return CrawlResult(
        url=url,
        source_type=source_type,
        title=title,
        price=_extract_price(text),
        rating=_extract_rating(text),
        extracted_text=text,
        html=html,
        reviews=parser.reviews,
        metadata={"extractor": "generic_html"},
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
