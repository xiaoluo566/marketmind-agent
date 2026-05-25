from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser

from app.crawler.errors import CrawlError, CrawlErrorCode
from app.crawler.schemas import CrawlResult

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

    def handle_starttag(self, tag: str, attrs) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
        if normalized_tag in {"title", "h1"}:
            self._active_tag = normalized_tag

    def handle_endtag(self, tag: str) -> None:
        normalized_tag = tag.lower()
        if normalized_tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1
        if self._active_tag == normalized_tag:
            self._active_tag = None

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = normalize_text(data)
        if not value:
            return
        self._text_parts.append(value)
        if self._active_tag == "title" and self.title is None:
            self.title = value
        if self._active_tag == "h1" and self.heading is None:
            self.heading = value

    def visible_text(self) -> str:
        return normalize_text(" ".join(self._text_parts))


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
