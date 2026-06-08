from __future__ import annotations

import json
from pathlib import Path

from app.benchmarking.main_path import (
    DEFAULT_STAGE_ORDER,
    build_fixture_benchmark_results,
    run_day27_fixture_benchmark,
)
from app.benchmarking.summary import (
    BenchmarkStageResult,
    BenchmarkTaskResult,
    summarize_benchmark_results,
    write_benchmark_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]


def read_project_file(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), f"{relative_path} should exist"
    return path.read_text(encoding="utf-8")


def test_benchmark_summary_computes_success_rate_stage_averages_and_bottlenecks() -> None:
    results = [
        BenchmarkTaskResult(
            task_id="tsk_1",
            source_id="fixture-1",
            status="completed",
            stages=[
                BenchmarkStageResult(name="api", duration_ms=10),
                BenchmarkStageResult(name="crawler", duration_ms=80),
                BenchmarkStageResult(name="rag", duration_ms=30),
            ],
        ),
        BenchmarkTaskResult(
            task_id="tsk_2",
            source_id="fixture-2",
            status="completed",
            stages=[
                BenchmarkStageResult(name="api", duration_ms=20),
                BenchmarkStageResult(name="crawler", duration_ms=100),
                BenchmarkStageResult(name="rag", duration_ms=40),
            ],
        ),
        BenchmarkTaskResult(
            task_id="tsk_3",
            source_id="fixture-3",
            status="failed",
            error_code="ACCESS_BLOCKED",
            stages=[
                BenchmarkStageResult(name="api", duration_ms=30),
                BenchmarkStageResult(name="crawler", duration_ms=120, success=False),
            ],
        ),
    ]

    summary = summarize_benchmark_results(results)

    assert summary.total_runs == 3
    assert summary.success_count == 2
    assert summary.failure_count == 1
    assert summary.success_rate == 0.6667
    assert summary.average_total_duration_ms == 143
    assert summary.stage_averages_ms["api"] == 20
    assert summary.stage_averages_ms["crawler"] == 100
    assert summary.failure_counts == {"ACCESS_BLOCKED": 1}
    assert summary.bottlenecks[0].stage == "crawler"
    assert summary.bottlenecks[0].average_duration_ms == 100


def test_day27_fixture_benchmark_generates_twenty_reproducible_samples() -> None:
    results = build_fixture_benchmark_results(iterations=20)
    summary = summarize_benchmark_results(results)

    assert len(results) == 20
    assert summary.total_runs == 20
    assert summary.success_count == 19
    assert summary.failure_count == 1
    assert summary.failure_counts == {"ACCESS_BLOCKED": 1}
    assert [stage.name for stage in results[0].stages] == list(DEFAULT_STAGE_ORDER)
    assert summary.bottlenecks[0].stage == "crawler"
    assert summary.bottlenecks[1].stage == "rag"
    assert summary.model_call_count == 0
    assert summary.total_tokens == 0


def test_benchmark_artifacts_write_machine_readable_json_and_markdown(tmp_path) -> None:
    output_dir = tmp_path / "benchmarks"
    results = build_fixture_benchmark_results(iterations=20)
    artifact = write_benchmark_artifacts(
        results=results,
        output_dir=output_dir,
        benchmark_name="day27-main-path-fixture",
    )

    payload = json.loads(artifact.json_path.read_text(encoding="utf-8"))
    markdown = artifact.markdown_path.read_text(encoding="utf-8")

    assert payload["benchmark_name"] == "day27-main-path-fixture"
    assert payload["summary"]["total_runs"] == 20
    assert payload["summary"]["failure_counts"] == {"ACCESS_BLOCKED": 1}
    assert len(payload["results"]) == 20
    assert "Day 27 主链路 Benchmark" in markdown
    assert "crawler" in markdown
    assert "ACCESS_BLOCKED" in markdown


def test_run_day27_fixture_benchmark_writes_default_artifacts(tmp_path) -> None:
    artifact = run_day27_fixture_benchmark(iterations=20, output_dir=tmp_path)

    assert artifact.summary.total_runs == 20
    assert artifact.json_path.exists()
    assert artifact.markdown_path.exists()
    assert artifact.summary_path.exists()


def test_day27_docs_record_benchmark_scope_and_artifacts() -> None:
    roadmap = read_project_file("doc/roadmap/day-27.md")
    development_log = read_project_file("doc/supporting/development-log.md")
    interview_dossier = read_project_file("doc/supporting/interview-defense-dossier.md")
    performance_doc = read_project_file("doc/supporting/performance-benchmark.md")
    llmops_metrics = read_project_file("doc/supporting/llmops-metrics.md")

    for expected in (
        "backend/app/benchmarking/main_path.py",
        "doc/supporting/day27-benchmark-results.json",
        "doc/supporting/day27-benchmark-summary.md",
        "20 个 fixture 样例任务",
    ):
        assert expected in roadmap

    assert "Day 27 开发记录" in development_log
    assert "Day 27 做性能 benchmark" in interview_dossier
    assert "Day 27 主链路 Benchmark" in performance_doc
    assert "Day 27 已落地 benchmark 指标" in llmops_metrics
