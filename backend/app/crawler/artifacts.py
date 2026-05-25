from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from app.crawler.schemas import CrawlArtifact


@dataclass(frozen=True, slots=True)
class SavedArtifact:
    artifact: CrawlArtifact
    path: Path


class LocalCrawlerArtifactStore:
    def __init__(self, base_dir: str | Path) -> None:
        self._base_dir = Path(base_dir)

    def save_text(
        self,
        *,
        task_id: str,
        artifact_type: str,
        content: str,
        extension: str = "html",
        mime_type: str = "text/html",
    ) -> SavedArtifact:
        safe_task_id = _sanitize_segment(task_id)
        safe_artifact_type = _sanitize_segment(artifact_type)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        target_dir = self._base_dir / safe_task_id
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{stamp}_{safe_artifact_type}.{extension}"
        path.write_text(content, encoding="utf-8")

        checksum = sha256(content.encode("utf-8")).hexdigest()
        artifact = CrawlArtifact(
            artifact_type=artifact_type,
            path=str(path),
            mime_type=mime_type,
            checksum=checksum,
            metadata={"task_id": task_id},
        )
        return SavedArtifact(artifact=artifact, path=path)


def _sanitize_segment(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return normalized or "artifact"
