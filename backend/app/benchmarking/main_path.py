from __future__ import annotations

import argparse
from pathlib import Path

from app.benchmarking.summary import (
    BenchmarkArtifact,
    BenchmarkStageResult,
    BenchmarkTaskResult,
    write_benchmark_artifacts,
)

DEFAULT_STAGE_ORDER = ("api", "queue", "crawler", "agent", "rag", "report")


def build_fixture_benchmark_results(iterations: int = 20) -> list[BenchmarkTaskResult]:
    if iterations < 1:
        raise ValueError("iterations must be greater than 0")

    return [_build_result(index) for index in range(1, iterations + 1)]


def run_day27_fixture_benchmark(
    *,
    iterations: int = 20,
    output_dir: Path | None = None,
) -> BenchmarkArtifact:
    results = build_fixture_benchmark_results(iterations=iterations)
    return write_benchmark_artifacts(
        results=results,
        output_dir=output_dir or Path("doc/supporting"),
        benchmark_name="day27-main-path-fixture",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the Day 27 fixture benchmark.")
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--output-dir", type=Path, default=Path("doc/supporting"))
    args = parser.parse_args(argv)

    artifact = run_day27_fixture_benchmark(
        iterations=args.iterations,
        output_dir=args.output_dir,
    )
    print(f"summary: {artifact.summary_path}")
    print(f"results: {artifact.json_path}")
    print(f"markdown: {artifact.markdown_path}")
    print(f"success_rate: {artifact.summary.success_rate:.2%}")
    return 0


def _build_result(index: int) -> BenchmarkTaskResult:
    is_failure = index == 13
    stages = _stage_results(index=index, failed=is_failure)

    return BenchmarkTaskResult(
        task_id=f"bench_tsk_{index:02d}",
        source_id=f"fixture-product-{index:02d}",
        status="failed" if is_failure else "completed",
        error_code="ACCESS_BLOCKED" if is_failure else None,
        stages=stages,
        model_call_count=0,
        input_tokens=0,
        output_tokens=0,
    )


def _stage_results(index: int, *, failed: bool) -> tuple[BenchmarkStageResult, ...]:
    durations = {
        "api": 11 + (index % 4) * 2,
        "queue": 6 + (index % 3),
        "crawler": 96 + (index % 5) * 15,
        "agent": 38 + (index % 4) * 8,
        "rag": 62 + (index % 6) * 9,
        "report": 50 + (index % 5) * 7,
    }
    if failed:
        return (
            BenchmarkStageResult(name="api", duration_ms=durations["api"]),
            BenchmarkStageResult(name="queue", duration_ms=durations["queue"]),
            BenchmarkStageResult(
                name="crawler",
                duration_ms=durations["crawler"] + 60,
                success=False,
                error_code="ACCESS_BLOCKED",
            ),
        )

    return tuple(
        BenchmarkStageResult(name=stage, duration_ms=durations[stage])
        for stage in DEFAULT_STAGE_ORDER
    )


if __name__ == "__main__":
    raise SystemExit(main())
