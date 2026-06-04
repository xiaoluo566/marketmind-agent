from __future__ import annotations

import html
import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReviewTextChunk:
    chunk_index: int
    content: str


def clean_review_text(raw_text: str) -> str:
    without_scripts = re.sub(
        r"<(script|style)\b[^>]*>.*?</\1>",
        " ",
        raw_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_tags = re.sub(r"<[^>]+>", " ", without_scripts)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def split_review_text(
    raw_text: str,
    *,
    max_chars: int = 500,
) -> list[ReviewTextChunk]:
    text = clean_review_text(raw_text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [ReviewTextChunk(chunk_index=0, content=text)]

    sentences = _split_sentences(text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
            continue
        candidate = f"{current} {sentence}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        chunks.extend(_force_split(current, max_chars=max_chars))
        current = sentence
    if current:
        chunks.extend(_force_split(current, max_chars=max_chars))

    return [
        ReviewTextChunk(chunk_index=index, content=content)
        for index, content in enumerate(chunk for chunk in chunks if chunk.strip())
    ]


def _split_sentences(text: str) -> list[str]:
    parts = re.findall(r"[^。！？!?\.]+[。！？!?\.]?", text)
    return [part.strip() for part in parts if part.strip()]


def _force_split(text: str, *, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]
