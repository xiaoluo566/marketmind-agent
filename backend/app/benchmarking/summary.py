from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class BenchmarkStageResult(BaseModel):
    name: str
    duration_ms: int = Field(ge=0)
    success: bool = True
    error_code: str | None = None


class BenchmarkTaskResult(BaseModel):
    task_id: str
    source_id: str
    status: Literal["completed", "failed"]
    stages: tuple[BenchmarkStageResult, ...]
    error_code: str | None = None
    model_call_count: int = Field(default=0, ge=0)
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)

    @computed_field
    @property
    def total_duration_ms(self) -> int:
        return sum(stage.duration_ms for stage in self.stages)

    @computed_field
    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


class BenchmarkBottleneck(BaseModel):
    stage: str
    average_duration_ms: int
    sample_count: int
    share_of_total: float


class BenchmarkSummary(BaseModel):
    total_runs: int
    success_count: int
    failure_count: int
    success_rate: float
    average_total_duration_ms: int
    p50_total_duration_ms: int
    p95_total_duration_ms: int
    stage_averages_ms: dict[str, int]
    failure_counts: dict[str, int]
    bottlenecks: tuple[BenchmarkBottleneck, ...]
    model_call_count: int
    total_tokens: int


@dataclass(frozen=True)
class BenchmarkArtifact:
    benchmark_name: str
    json_path: Path
    markdown_path: Path
    summary_path: Path
    summary: BenchmarkSummary


def summarize_benchmark_results(results: list[BenchmarkTaskResult]) -> BenchmarkSummary:
    if not results:
        return BenchmarkSummary(
            total_runs=0,
            success_count=0,
            failure_count=0,
            success_rate=0,
            average_total_duration_ms=0,
            p50_total_duration_ms=0,
            p95_total_duration_ms=0,
            stage_averages_ms={},
            failure_counts={},
            bottlenecks=(),
            model_call_count=0,
            total_tokens=0,
        )

    total_runs = len(results)
    success_count = sum(1 for result in results if result.status == "completed")
    failure_count = total_runs - success_count
    total_durations = [result.total_duration_ms for result in results]
    stage_samples = _stage_samples(results)
    stage_averages = {
        stage: _rounded_average(samples) for stage, samples in sorted(stage_samples.items())
    }
    average_total = _rounded_average(total_durations)
    failure_counts = _failure_counts(results)

    return BenchmarkSummary(
        total_runs=total_runs,
        success_count=success_count,
        failure_count=failure_count,
        success_rate=round(success_count / total_runs, 4),
        average_total_duration_ms=average_total,
        p50_total_duration_ms=_percentile(total_durations, 50),
        p95_total_duration_ms=_percentile(total_durations, 95),
        stage_averages_ms=stage_averages,
        failure_counts=failure_counts,
        bottlenecks=_bottlenecks(stage_samples=stage_samples, average_total=average_total),
        model_call_count=sum(result.model_call_count for result in results),
        total_tokens=sum(result.total_tokens for result in results),
    )


def write_benchmark_artifacts(
    *,
    results: list[BenchmarkTaskResult],
    output_dir: Path,
    benchmark_name: str,
) -> BenchmarkArtifact:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_benchmark_results(results)
    json_path = output_dir / "day27-benchmark-results.json"
    markdown_path = output_dir / "day27-benchmark-summary.md"
    summary_path = output_dir / "day27-benchmark-summary.json"

    json_payload = {
        "benchmark_name": benchmark_name,
        "scope": (
            "local fixture benchmark; no live Redis, Celery broker, "
            "external website, or LLM API"
        ),
        "summary": summary.model_dump(mode="json"),
        "results": [result.model_dump(mode="json") for result in results],
    }
    summary_payload = {
        "benchmark_name": benchmark_name,
        "summary": summary.model_dump(mode="json"),
    }

    json_path.write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(_render_markdown(summary=summary, results=results), encoding="utf-8")

    return BenchmarkArtifact(
        benchmark_name=benchmark_name,
        json_path=json_path,
        markdown_path=markdown_path,
        summary_path=summary_path,
        summary=summary,
    )


def _stage_samples(results: list[BenchmarkTaskResult]) -> dict[str, list[int]]:
    samples: dict[str, list[int]] = defaultdict(list)
    for result in results:
        for stage in result.stages:
            samples[stage.name].append(stage.duration_ms)
    return dict(samples)


def _failure_counts(results: list[BenchmarkTaskResult]) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for result in results:
        if result.status == "failed":
            counter[result.error_code or "UNKNOWN_FAILURE"] += 1
    return dict(sorted(counter.items()))


def _bottlenecks(
    *,
    stage_samples: dict[str, list[int]],
    average_total: int,
) -> tuple[BenchmarkBottleneck, ...]:
    bottlenecks = [
        BenchmarkBottleneck(
            stage=stage,
            average_duration_ms=_rounded_average(samples),
            sample_count=len(samples),
            share_of_total=round(_rounded_average(samples) / average_total, 4)
            if average_total
            else 0,
        )
        for stage, samples in stage_samples.items()
    ]
    return tuple(
        sorted(
            bottlenecks,
            key=lambda item: (item.average_duration_ms, item.sample_count, item.stage),
            reverse=True,
        )
    )


def _rounded_average(values: list[int]) -> int:
    if not values:
        return 0
    return round(sum(values) / len(values))


def _percentile(values: list[int], percentile: int) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, ceil((percentile / 100) * len(ordered)) - 1)
    return ordered[index]


def _render_markdown(
    *,
    summary: BenchmarkSummary,
    results: list[BenchmarkTaskResult],
) -> str:
    bottleneck_rows = "\n".join(
        f"| {item.stage} | {item.average_duration_ms} | {item.sample_count} | "
        f"{item.share_of_total:.2%} |"
        for item in summary.bottlenecks
    )
    failure_rows = "\n".join(
        f"| {code} | {count} |" for code, count in summary.failure_counts.items()
    ) or "| 无 | 0 |"
    result_rows = "\n".join(
        f"| {result.task_id} | {result.source_id} | {result.status} | "
        f"{result.total_duration_ms} | {result.error_code or '-'} |"
        for result in results
    )

    return (
        "# Day 27 主链路 Benchmark\n\n"
        "这份结果来自 20 个 fixture 样例任务，目标是稳定复现主链路各阶段耗时。"
        "当前不代表真实外部网站、真实 Redis/Celery broker 或真实 LLM API 性能。\n\n"
        "## 总览\n\n"
        f"- 样本数：{summary.total_runs}\n"
        f"- 成功数：{summary.success_count}\n"
        f"- 失败数：{summary.failure_count}\n"
        f"- 成功率：{summary.success_rate:.2%}\n"
        f"- 平均端到端耗时：{summary.average_total_duration_ms} ms\n"
        f"- P50 端到端耗时：{summary.p50_total_duration_ms} ms\n"
        f"- P95 端到端耗时：{summary.p95_total_duration_ms} ms\n"
        f"- 模型调用次数：{summary.model_call_count}\n"
        f"- Token 总量：{summary.total_tokens}\n\n"
        "## 阶段瓶颈\n\n"
        "| 阶段 | 平均耗时 ms | 样本数 | 平均占比 |\n"
        "| --- | ---: | ---: | ---: |\n"
        f"{bottleneck_rows}\n\n"
        "## 失败分类\n\n"
        "| 错误码 | 次数 |\n"
        "| --- | ---: |\n"
        f"{failure_rows}\n\n"
        "## 样例任务\n\n"
        "| task_id | source_id | status | total_duration_ms | error_code |\n"
        "| --- | --- | --- | ---: | --- |\n"
        f"{result_rows}\n"
    )
