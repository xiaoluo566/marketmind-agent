from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt


class AgentToolDecision(BaseModel):
    thought: str = Field(min_length=1)
    action: str = Field(default="call_tool")
    tool_name: str = Field(min_length=1)
    tool_input: dict[str, Any] = Field(default_factory=dict)


class ReportStructure(BaseModel):
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    sections: list[str] = Field(default_factory=list)


TModel = TypeVar("TModel", bound=BaseModel)
RepairFn = Callable[[str], str]


@dataclass(frozen=True, slots=True)
class StructuredOutputParseResult:
    output: BaseModel
    raw_output: str
    repaired_output: str | None
    prompt_name: str
    validation_error_count: int
    self_heal_count: int
    self_healed: bool
    attempts: list[dict[str, Any]]


class StructuredOutputGuardrailError(ValueError):
    def __init__(
        self,
        *,
        prompt_name: str,
        raw_output: str,
        validation_error_count: int,
        self_heal_count: int,
        details: dict[str, Any],
    ) -> None:
        super().__init__("structured output could not be parsed")
        self.prompt_name = prompt_name
        self.original_output = raw_output
        self.validation_error_count = validation_error_count
        self.self_heal_count = self_heal_count
        self.details = details


class StructuredOutputGuardrail:
    def __init__(
        self,
        *,
        max_self_heal_attempts: int = 1,
        repair_retry_attempts: int = 2,
    ) -> None:
        self._max_self_heal_attempts = max(0, max_self_heal_attempts)
        self._repair_retry_attempts = max(1, repair_retry_attempts)

    def parse(
        self,
        raw_output: str,
        *,
        schema: type[TModel],
        prompt_name: str,
        repair: RepairFn | None = None,
    ) -> StructuredOutputParseResult:
        candidate = raw_output
        validation_error_count = 0
        attempts: list[dict[str, Any]] = []

        for attempt_index in range(self._max_self_heal_attempts + 1):
            try:
                payload = _load_json(candidate)
                output = schema.model_validate(payload)
                self_healed = candidate != raw_output and validation_error_count > 0
                return StructuredOutputParseResult(
                    output=output,
                    raw_output=raw_output,
                    repaired_output=candidate if candidate != raw_output else None,
                    prompt_name=prompt_name,
                    validation_error_count=validation_error_count,
                    self_heal_count=1 if self_healed else 0,
                    self_healed=self_healed,
                    attempts=attempts,
                )
            except (json.JSONDecodeError, ValidationError) as exc:
                validation_error_count += 1
                attempts.append(
                    {
                        "attempt": attempt_index + 1,
                        "candidate": candidate,
                        "error": str(exc),
                    }
                )
                if attempt_index >= self._max_self_heal_attempts:
                    break
                if repair is None:
                    break

                prompt = build_json_repair_prompt(
                    raw_output=raw_output,
                    schema_name=schema.__name__,
                    error_message=str(exc),
                    prompt_name=prompt_name,
                )
                candidate = self._call_repair(repair, prompt)

        raise StructuredOutputGuardrailError(
            prompt_name=prompt_name,
            raw_output=raw_output,
            validation_error_count=validation_error_count,
            self_heal_count=0,
            details={"attempts": attempts},
        )

    def _call_repair(self, repair: RepairFn, prompt: str) -> str:
        retryable = retry(
            retry=retry_if_exception_type(Exception),
            stop=stop_after_attempt(self._repair_retry_attempts),
            reraise=True,
        )(repair)
        return retryable(prompt)


def build_json_repair_prompt(
    *,
    raw_output: str,
    schema_name: str,
    error_message: str,
    prompt_name: str,
) -> str:
    return (
        f"Prompt name: {prompt_name}\n"
        f"Schema: {schema_name}\n"
        f"Error: {error_message}\n"
        "Please return only valid JSON that matches the schema.\n"
        f"Raw output:\n{raw_output}"
    )


def _load_json(raw_output: str) -> Any:
    text = raw_output.strip()
    fenced = _extract_fenced_json(text)
    if fenced is not None:
        text = fenced

    if not text.startswith("{") and not text.startswith("["):
        extracted = _extract_braced_json(text)
        if extracted is not None:
            text = extracted

    return json.loads(text)


def _extract_fenced_json(text: str) -> str | None:
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fence_match is None:
        return None
    return fence_match.group(1).strip()


def _extract_braced_json(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1].strip()
