from enum import StrEnum
from typing import Any


class CrawlErrorCode(StrEnum):
    PAGE_TIMEOUT = "PAGE_TIMEOUT"
    DOM_NOT_FOUND = "DOM_NOT_FOUND"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    NETWORK_ERROR = "NETWORK_ERROR"
    PARSER_ERROR = "PARSER_ERROR"
    UNKNOWN_SITE = "UNKNOWN_SITE"


class CrawlError(RuntimeError):
    def __init__(
        self,
        code: CrawlErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}
