# Day 27 - 性能与容量评估

## 当天目标

Day 27 的目标是用可复现数据判断系统瓶颈，而不是凭感觉优化。今天要建立第一版 benchmark harness，输出机器可读 JSON 和人可读 Markdown，用于后续 Day 28 失败重试、Day 29 demo、Day 30 复盘和简历指标沉淀。

今天的 benchmark 明确是本地 fixture 基准，不代表真实线上流量：

- 不连接真实 Redis / Celery broker。
- 不访问真实外部电商网站。
- 不调用真实 LLM / embedding API。
- 不声明真实 token 成本。
- 不把 Docker Compose build/up 当成已完成。

它解决的是第一阶段性能问题：系统主链路各阶段耗时统计、失败分类统计、瓶颈排序和结果 artifact 固化。

## 前置依赖

- `day-24.md`：主链路集成回归已经证明 API、Worker、Crawler fixture、RAG、Report 和 Evidence API 可以闭环。
- `day-25.md`：Docker Compose 拓扑已经固化，但真实 build/up 仍待 Docker daemon 可用后补验。
- `day-26.md`：CI 与版本回退流程已经建立，benchmark 代码可以进入质量门禁。
- `../supporting/llmops-metrics.md`：定义需要收集的 LLMOps 与任务指标。
- `../supporting/observability.md`：定义 trace、duration、error layer 和错误分类。

## 当天交付物

- `backend/app/benchmarking/summary.py`
- `backend/app/benchmarking/main_path.py`
- `tests/test_day27_benchmarking.py`
- `doc/supporting/day27-benchmark-results.json`
- `doc/supporting/day27-benchmark-summary.json`
- `doc/supporting/day27-benchmark-summary.md`
- `doc/supporting/performance-benchmark.md`
- `doc/supporting/llmops-metrics.md` Day 27 指标补充
- `doc/supporting/development-log.md` Day 27 开发记录
- `doc/supporting/interview-defense-dossier.md` Day 27 面试表达补充

## 实际完成内容

### 1. Benchmark 数据模型

新增 `backend/app/benchmarking/summary.py`，定义：

| 模型 / 函数 | 作用 |
| --- | --- |
| `BenchmarkStageResult` | 单个阶段耗时、成功状态和错误码 |
| `BenchmarkTaskResult` | 单个样例任务的状态、阶段列表、模型调用次数和 token |
| `BenchmarkSummary` | 总样本数、成功率、平均耗时、P50、P95、阶段均值、失败分类和瓶颈排序 |
| `summarize_benchmark_results()` | 从任务结果生成汇总 |
| `write_benchmark_artifacts()` | 写出 JSON、summary JSON 和 Markdown |

当前阶段列表：

```text
api -> queue -> crawler -> agent -> rag -> report
```

### 2. Fixture 主链路 benchmark 脚本

新增 `backend/app/benchmarking/main_path.py`，提供：

- `build_fixture_benchmark_results(iterations=20)`
- `run_day27_fixture_benchmark(iterations=20, output_dir=Path("doc/supporting"))`
- CLI 入口：`python -m app.benchmarking.main_path`

运行命令：

```powershell
$env:PYTHONPATH='backend'
uv run python -m app.benchmarking.main_path --iterations 20 --output-dir doc\supporting
```

生成文件：

- `doc/supporting/day27-benchmark-results.json`
- `doc/supporting/day27-benchmark-summary.json`
- `doc/supporting/day27-benchmark-summary.md`

### 3. Benchmark 契约测试

新增 `tests/test_day27_benchmarking.py`，覆盖：

- 成功率、失败数、平均耗时、阶段均值和瓶颈排序。
- 20 个 fixture 样例任务可复现生成。
- 失败分类固定为 `ACCESS_BLOCKED`。
- JSON 和 Markdown artifact 可写出。
- Day27 roadmap、development log、interview dossier、performance benchmark 和 LLMOps 文档必须记录 benchmark 边界和 artifact。

### 4. Day27 实测结果

当前结果来自 20 个 fixture 样例任务：

| 指标 | 结果 |
| --- | ---: |
| 样本数 | 20 |
| 成功数 | 19 |
| 失败数 | 1 |
| 成功率 | 95.00% |
| 平均端到端耗时 | 338 ms |
| P50 端到端耗时 | 347 ms |
| P95 端到端耗时 | 391 ms |
| 模型调用次数 | 0 |
| Token 总量 | 0 |

阶段瓶颈：

| 排名 | 阶段 | 平均耗时 | 平均占比 |
| --- | --- | ---: | ---: |
| 1 | crawler | 129 ms | 38.17% |
| 2 | rag | 84 ms | 24.85% |
| 3 | report | 64 ms | 18.93% |
| 4 | agent | 50 ms | 14.79% |
| 5 | api | 14 ms | 4.14% |
| 6 | queue | 7 ms | 2.07% |

失败分类：

| 错误码 | 次数 |
| --- | ---: |
| `ACCESS_BLOCKED` | 1 |

## 当天为什么这样选

### 为什么先做 fixture benchmark？

真实外部网站、真实浏览器集群、真实 Redis/Celery broker 和真实 LLM API 都会引入大量波动。Day 27 的首要目标不是得到“最好看的数字”，而是建立稳定的指标结构和 artifact 格式。

fixture benchmark 的好处：

- 每次运行结果可复现。
- 可以被自动化测试覆盖。
- 可以稳定验证统计逻辑。
- 可以明确区分业务阶段瓶颈。
- 不会因为外部网站或模型服务波动误判系统性能。

### 为什么记录 0 次模型调用和 0 token？

当前 Day27 benchmark 没有接真实 LLM / embedding API，所以必须诚实记录模型调用次数为 0，token 总量为 0。这样后续接真实 provider 后，指标变化可以清楚对比，而不是把 fake 数据伪装成真实成本。

### 为什么把 artifact 写入文档目录？

Day27 结果不只是一次命令输出，而是后续简历、面试、Day30 复盘和 regression 对比的依据。写入 `doc/supporting/` 的 JSON 和 Markdown 后，可以：

- 被 Git 版本管理追踪。
- 被测试检查是否存在。
- 被面试文档引用。
- 和后续真实 benchmark 结果做差异对比。

## 验证命令

```powershell
uv run pytest tests\test_day27_benchmarking.py
$env:PYTHONPATH='backend'; uv run python -m app.benchmarking.main_path --iterations 20 --output-dir doc\supporting
```

收尾时还需要跑完整门禁：

```powershell
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

当前验证结果：

```text
Day 27 benchmark tests: 5 passed
Day 26 + Day 27 targeted tests: 9 passed
benchmark script: generated day27-benchmark-results.json, day27-benchmark-summary.json, day27-benchmark-summary.md
uv run pytest: 150 passed
uv run pytest --cov=backend --cov-report=term-missing: 150 passed, backend coverage 90.80%, fail-under 80 reached
uv run ruff check backend tests migrations: All checks passed
uv run alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend npm run lint: passed
frontend npm run build: passed
frontend npm audit --audit-level=high: found 0 vulnerabilities
uvx pip-audit: No known vulnerabilities found
```

## 遗留问题

- 当前 benchmark 是 fixture benchmark，不代表真实外部网站性能。
- 当前没有接真实 Redis / Celery broker，因此 queue 阶段只是本地模拟耗时。
- 当前没有真实 LLM / embedding API，所以模型调用和 token 成本为 0。
- 当前还没有并发 benchmark。
- 当前还没有把 benchmark 输出接入前端 LLMOps 面板。
- Day 28 做 retry / resume 时，需要用 Day27 的失败分类结构继续扩展重试成功率指标。

## 关联文档

- 上一天：`day-26.md`
- 下一天：`day-28.md`
- 指标：`../supporting/llmops-metrics.md`
- 可观测性：`../supporting/observability.md`
- 性能报告：`../supporting/performance-benchmark.md`
- 简历：`../supporting/resume-story.md`

## 建议提交

```text
perf: 增加 Day 27 主链路 benchmark
```
