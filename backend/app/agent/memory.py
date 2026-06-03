from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, Protocol

from pydantic import BaseModel, Field
from redis import Redis
from redis.exceptions import RedisError

from app.storage.agent_stores import AgentStepData


class AgentMemoryStoreUnavailableError(RuntimeError):
    pass


class AgentMemoryEntry(BaseModel):
    sequence: int = Field(ge=1)
    step_type: str = Field(min_length=1)
    content: str = Field(default="")
    evidence_refs: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentMemorySnapshot(BaseModel):
    task_id: str
    summary: str = ""
    summary_evidence_refs: list[str] = Field(default_factory=list)
    recent_entries: list[AgentMemoryEntry] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def evidence_refs(self) -> list[str]:
        refs: list[str] = []
        refs.extend(self.summary_evidence_refs)
        for entry in self.recent_entries:
            refs.extend(entry.evidence_refs)
        return _dedupe(refs)


class AgentPromptContext(BaseModel):
    task_id: str
    summary: str
    recent_entries: list[AgentMemoryEntry]
    evidence_refs: list[str]

    def to_prompt_text(self) -> str:
        sections: list[str] = []
        if self.summary:
            sections.append(f"历史摘要：\n{self.summary}")
        if self.recent_entries:
            recent = "\n".join(
                f"- step {entry.sequence} {entry.step_type}: {entry.content}"
                for entry in self.recent_entries
            )
            sections.append(f"最近上下文：\n{recent}")
        if self.evidence_refs:
            sections.append(f"证据引用：{', '.join(self.evidence_refs)}")
        return "\n\n".join(sections)


class AgentMemoryStore(Protocol):
    def save(self, snapshot: AgentMemorySnapshot) -> AgentMemorySnapshot: ...

    def get(self, task_id: str) -> AgentMemorySnapshot | None: ...


class InMemoryAgentMemoryStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, AgentMemorySnapshot] = {}

    def save(self, snapshot: AgentMemorySnapshot) -> AgentMemorySnapshot:
        next_snapshot = snapshot.model_copy(deep=True)
        self._snapshots[next_snapshot.task_id] = next_snapshot
        return next_snapshot.model_copy(deep=True)

    def get(self, task_id: str) -> AgentMemorySnapshot | None:
        snapshot = self._snapshots.get(task_id)
        if snapshot is None:
            return None
        return snapshot.model_copy(deep=True)


class RedisAgentMemoryStore:
    def __init__(
        self,
        *,
        redis_url: str,
        ttl_seconds: int,
        key_prefix: str = "marketmind:agent:memory",
    ) -> None:
        self._client = Redis.from_url(redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds
        self._key_prefix = key_prefix

    def save(self, snapshot: AgentMemorySnapshot) -> AgentMemorySnapshot:
        try:
            self._client.set(
                self._key(snapshot.task_id),
                snapshot.model_dump_json(),
                ex=self._ttl_seconds,
            )
        except RedisError as exc:
            raise AgentMemoryStoreUnavailableError(str(exc)) from exc
        return snapshot

    def get(self, task_id: str) -> AgentMemorySnapshot | None:
        try:
            raw_snapshot = self._client.get(self._key(task_id))
        except RedisError as exc:
            raise AgentMemoryStoreUnavailableError(str(exc)) from exc
        if raw_snapshot is None:
            return None
        return AgentMemorySnapshot.model_validate_json(raw_snapshot)

    def _key(self, task_id: str) -> str:
        return f"{self._key_prefix}:{task_id}"


class AgentShortTermMemory:
    def __init__(
        self,
        *,
        store: AgentMemoryStore,
        window_size: int = 3,
        max_summary_chars: int = 1_200,
    ) -> None:
        self._store = store
        self._window_size = max(1, window_size)
        self._max_summary_chars = max(80, max_summary_chars)

    def load_context(self, task_id: str) -> AgentMemorySnapshot:
        snapshot = self._store.get(task_id)
        if snapshot is None:
            return AgentMemorySnapshot(task_id=task_id)
        return snapshot

    def build_prompt_context(self, task_id: str) -> AgentPromptContext:
        snapshot = self.load_context(task_id)
        return AgentPromptContext(
            task_id=task_id,
            summary=snapshot.summary,
            recent_entries=snapshot.recent_entries,
            evidence_refs=snapshot.evidence_refs,
        )

    def append_entry(
        self,
        task_id: str,
        entry: AgentMemoryEntry,
    ) -> AgentMemorySnapshot:
        snapshot = self.load_context(task_id)
        next_entries = [item.model_copy(deep=True) for item in snapshot.recent_entries]
        next_entries.append(entry.model_copy(deep=True))

        next_snapshot = AgentMemorySnapshot(
            task_id=task_id,
            summary=snapshot.summary,
            summary_evidence_refs=snapshot.summary_evidence_refs,
            recent_entries=next_entries,
            updated_at=datetime.now(UTC),
        )
        return self._store.save(self._compact(next_snapshot))

    def remember_step(self, step: AgentStepData) -> AgentMemorySnapshot:
        return self.append_entry(
            step.task_id,
            memory_entry_from_step(step),
        )

    def restore_from_steps(
        self,
        *,
        task_id: str,
        steps: Iterable[AgentStepData],
    ) -> AgentMemorySnapshot:
        snapshot = AgentMemorySnapshot(task_id=task_id)
        for step in sorted(steps, key=lambda item: item.step_index):
            snapshot = AgentMemorySnapshot(
                task_id=task_id,
                summary=snapshot.summary,
                summary_evidence_refs=snapshot.summary_evidence_refs,
                recent_entries=[
                    *snapshot.recent_entries,
                    memory_entry_from_step(step),
                ],
                updated_at=datetime.now(UTC),
            )
            snapshot = self._compact(snapshot)
        return self._store.save(snapshot)

    def _compact(self, snapshot: AgentMemorySnapshot) -> AgentMemorySnapshot:
        if len(snapshot.recent_entries) <= self._window_size:
            return snapshot

        old_entries = snapshot.recent_entries[: -self._window_size]
        recent_entries = snapshot.recent_entries[-self._window_size :]
        summary = self._merge_summary(snapshot.summary, old_entries)
        summary_evidence_refs = _dedupe(
            [
                *snapshot.summary_evidence_refs,
                *[ref for entry in old_entries for ref in entry.evidence_refs],
            ]
        )
        return AgentMemorySnapshot(
            task_id=snapshot.task_id,
            summary=summary,
            summary_evidence_refs=summary_evidence_refs,
            recent_entries=recent_entries,
            updated_at=datetime.now(UTC),
        )

    def _merge_summary(self, current_summary: str, entries: list[AgentMemoryEntry]) -> str:
        lines = [current_summary.strip()] if current_summary.strip() else []
        for entry in entries:
            evidence_text = ""
            if entry.evidence_refs:
                evidence_text = f" evidence={','.join(entry.evidence_refs)}"
            lines.append(
                f"step {entry.sequence} {entry.step_type}: "
                f"{_truncate(entry.content, 180)}{evidence_text}"
            )
        summary = "\n".join(line for line in lines if line)
        return _tail(summary, self._max_summary_chars)


def memory_entry_from_step(step: AgentStepData) -> AgentMemoryEntry:
    content = _content_from_step(step)
    return AgentMemoryEntry(
        sequence=step.step_index,
        step_type=step.step_type,
        content=content,
        evidence_refs=extract_evidence_refs(step.tool_output),
        metadata={
            "agent_run_id": step.agent_run_id,
            "step_id": step.step_id,
            "status": step.status,
            "tool_name": step.tool_name,
        },
    )


def extract_evidence_refs(payload: Any) -> list[str]:
    refs: list[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {
                    "artifact_id",
                    "artifact_ids",
                    "review_id",
                    "review_ids",
                    "chunk_id",
                    "chunk_ids",
                    "evidence_ref",
                    "evidence_refs",
                }:
                    refs.extend(_coerce_refs(item))
                elif key == "checksum" and value.get("uri"):
                    refs.append(f"artifact:{item}")
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(payload)
    return _dedupe(refs)


def _content_from_step(step: AgentStepData) -> str:
    if step.step_type == "action" and step.tool_name:
        return f"调用工具 {step.tool_name}，参数：{step.tool_input}"
    if step.observation:
        return step.observation
    if step.thought:
        return step.thought
    if step.tool_name:
        return f"调用工具 {step.tool_name}，参数：{step.tool_input}"
    if step.error_message:
        return step.error_message
    return ""


def _coerce_refs(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _dedupe(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."


def _tail(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:].lstrip()


__all__ = [
    "AgentMemoryEntry",
    "AgentMemorySnapshot",
    "AgentMemoryStoreUnavailableError",
    "AgentPromptContext",
    "AgentShortTermMemory",
    "InMemoryAgentMemoryStore",
    "RedisAgentMemoryStore",
    "extract_evidence_refs",
    "memory_entry_from_step",
]
