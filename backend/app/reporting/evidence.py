from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.reporting.schemas import StructuredReport
from app.storage.models import AgentStep, Artifact, Review, ReviewChunk

EvidenceRefType = Literal["chunk", "review", "artifact", "step"]


class EvidenceRef(BaseModel):
    evidence_ref: str
    ref_type: EvidenceRefType
    source_id: str


class EvidenceSource(BaseModel):
    evidence_ref: str
    source_type: str
    source_id: str
    task_id: str | None = None
    available: bool = True
    title: str | None = None
    content_preview: str | None = None
    source_url: str | None = None
    parent_refs: list[str] = Field(default_factory=list)
    missing_reason: str | None = None
    metadata: dict = Field(default_factory=dict)


class EvidenceChain(BaseModel):
    task_id: str
    evidence_refs: list[str] = Field(default_factory=list)
    sources: list[EvidenceSource] = Field(default_factory=list)
    missing_refs: list[str] = Field(default_factory=list)


class SQLAlchemyEvidenceChainStore:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def resolve(self, *, task_id: str, evidence_refs: list[str]) -> EvidenceChain:
        sources: list[EvidenceSource] = []
        missing_refs: list[str] = []
        with self._session_scope() as session:
            for evidence_ref in _dedupe_refs(evidence_refs):
                try:
                    parsed = parse_evidence_ref(evidence_ref)
                except ValueError:
                    sources.append(
                        _missing_source(
                            evidence_ref=evidence_ref,
                            missing_reason="INVALID_EVIDENCE_REF",
                        )
                    )
                    missing_refs.append(evidence_ref)
                    continue

                source = self._resolve_one(session, task_id=task_id, parsed=parsed)
                sources.append(source)
                if not source.available:
                    missing_refs.append(evidence_ref)

        return EvidenceChain(
            task_id=task_id,
            evidence_refs=_dedupe_refs(evidence_refs),
            sources=sources,
            missing_refs=missing_refs,
        )

    @contextmanager
    def _session_scope(self):
        session = self._session_factory()
        try:
            yield session
        finally:
            session.close()

    def _resolve_one(
        self,
        session: Session,
        *,
        task_id: str,
        parsed: EvidenceRef,
    ) -> EvidenceSource:
        if parsed.ref_type == "chunk":
            return self._resolve_chunk(session, task_id=task_id, parsed=parsed)
        if parsed.ref_type == "review":
            return self._resolve_review(session, task_id=task_id, parsed=parsed)
        if parsed.ref_type == "artifact":
            return self._resolve_artifact(session, task_id=task_id, parsed=parsed)
        if parsed.ref_type == "step":
            return self._resolve_step(session, task_id=task_id, parsed=parsed)
        return _missing_source(
            evidence_ref=parsed.evidence_ref,
            missing_reason="UNSUPPORTED_EVIDENCE_REF",
        )

    def _resolve_chunk(
        self,
        session: Session,
        *,
        task_id: str,
        parsed: EvidenceRef,
    ) -> EvidenceSource:
        chunk = session.get(ReviewChunk, parsed.source_id)
        if chunk is None or chunk.task_id != task_id:
            return _missing_source(
                evidence_ref=parsed.evidence_ref,
                missing_reason="EVIDENCE_NOT_FOUND",
            )
        review = session.get(Review, chunk.review_id)
        metadata = dict(chunk.metadata_ or {})
        if review is not None:
            metadata.update(
                {
                    "review_external_id": review.external_id,
                    "rating": review.rating,
                    "source_type": review.source_type,
                }
            )
        return EvidenceSource(
            evidence_ref=parsed.evidence_ref,
            source_type="review_chunk",
            source_id=chunk.id,
            task_id=chunk.task_id,
            title=f"Review chunk #{chunk.chunk_index}",
            content_preview=_preview(chunk.content),
            source_url=review.source_url if review is not None else metadata.get("source_url"),
            parent_refs=[f"review:{chunk.review_id}"],
            metadata={
                **metadata,
                "chunk_index": chunk.chunk_index,
                "embedding_model": chunk.embedding_model,
                "embedding_dimensions": chunk.embedding_dimensions,
            },
        )

    def _resolve_review(
        self,
        session: Session,
        *,
        task_id: str,
        parsed: EvidenceRef,
    ) -> EvidenceSource:
        review = session.get(Review, parsed.source_id)
        if review is None or review.task_id != task_id:
            return _missing_source(
                evidence_ref=parsed.evidence_ref,
                missing_reason="EVIDENCE_NOT_FOUND",
            )
        return EvidenceSource(
            evidence_ref=parsed.evidence_ref,
            source_type="review",
            source_id=review.id,
            task_id=review.task_id,
            title=review.external_id or review.id,
            content_preview=_preview(review.content),
            source_url=review.source_url,
            parent_refs=[f"product:{review.product_id}"],
            metadata={
                **dict(review.raw_payload or {}),
                "rating": review.rating,
                "source_type": review.source_type,
            },
        )

    def _resolve_artifact(
        self,
        session: Session,
        *,
        task_id: str,
        parsed: EvidenceRef,
    ) -> EvidenceSource:
        artifact = session.get(Artifact, parsed.source_id)
        if artifact is None or artifact.task_id != task_id:
            return _missing_source(
                evidence_ref=parsed.evidence_ref,
                missing_reason="EVIDENCE_NOT_FOUND",
            )
        metadata = dict(artifact.metadata_ or {})
        return EvidenceSource(
            evidence_ref=parsed.evidence_ref,
            source_type="artifact",
            source_id=artifact.id,
            task_id=artifact.task_id,
            title=artifact.artifact_type,
            content_preview=artifact.uri,
            source_url=metadata.get("source_url") or artifact.uri,
            parent_refs=[],
            metadata={
                **metadata,
                "artifact_type": artifact.artifact_type,
                "mime_type": artifact.mime_type,
                "checksum": artifact.checksum,
                "uri": artifact.uri,
            },
        )

    def _resolve_step(
        self,
        session: Session,
        *,
        task_id: str,
        parsed: EvidenceRef,
    ) -> EvidenceSource:
        step = session.get(AgentStep, parsed.source_id)
        if step is None or step.task_id != task_id:
            return _missing_source(
                evidence_ref=parsed.evidence_ref,
                missing_reason="EVIDENCE_NOT_FOUND",
            )
        return EvidenceSource(
            evidence_ref=parsed.evidence_ref,
            source_type="agent_step",
            source_id=step.id,
            task_id=step.task_id,
            title=f"{step.step_type}:{step.tool_name or 'none'}",
            content_preview=_preview(step.observation or step.thought or ""),
            source_url=None,
            parent_refs=[f"agent_run:{step.agent_run_id}"],
            metadata={
                "step_index": step.step_index,
                "step_type": step.step_type,
                "status": step.status,
                "tool_name": step.tool_name,
                "tool_input_keys": sorted((step.tool_input or {}).keys()),
                "tool_output_keys": sorted((step.tool_output or {}).keys()),
                "error_code": _tool_error_code(step.tool_output or {}),
            },
        )


def parse_evidence_ref(evidence_ref: str) -> EvidenceRef:
    parts = evidence_ref.split(":", maxsplit=1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(f"invalid evidence ref: {evidence_ref}")

    ref_type, source_id = parts
    supported_types = {"chunk", "review", "artifact", "step"}
    if ref_type not in supported_types:
        raise ValueError(f"unsupported evidence ref type: {ref_type}")

    return EvidenceRef(
        evidence_ref=evidence_ref,
        ref_type=ref_type,  # type: ignore[arg-type]
        source_id=source_id,
    )


def attach_evidence_chain(report: StructuredReport, chain: EvidenceChain) -> StructuredReport:
    return report.model_copy(
        deep=True,
        update={
            "metadata": {
                **report.metadata,
                "evidence_chain": chain.model_dump(mode="json"),
            }
        },
    )


def _missing_source(*, evidence_ref: str, missing_reason: str) -> EvidenceSource:
    return EvidenceSource(
        evidence_ref=evidence_ref,
        source_type="missing",
        source_id=evidence_ref.split(":", maxsplit=1)[-1],
        available=False,
        missing_reason=missing_reason,
    )


def _dedupe_refs(evidence_refs: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for evidence_ref in evidence_refs:
        if evidence_ref in seen:
            continue
        seen.add(evidence_ref)
        deduped.append(evidence_ref)
    return deduped


def _preview(value: str, max_length: int = 280) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3]}..."


def _tool_error_code(tool_output: dict) -> str | None:
    error = tool_output.get("error")
    if isinstance(error, dict):
        code = error.get("code")
        return code if isinstance(code, str) else None
    return None
