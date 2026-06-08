# 性能 Benchmark 记录

## 文档定位

这份文档记录 MarketMind Agent 的性能与容量评估。它不是宣传材料，所有数据都必须说明来源、样本规模、运行边界和不能代表什么。

Day 27 开始，benchmark 输出同时保留三类 artifact：

- 机器可读明细：`day27-benchmark-results.json`
- 机器可读摘要：`day27-benchmark-summary.json`
- 人可读摘要：`day27-benchmark-summary.md`

## Day 27 主链路 Benchmark

### 运行命令

```powershell
$env:PYTHONPATH='backend'
uv run python -m app.benchmarking.main_path --iterations 20 --output-dir doc\supporting
```

### 运行边界

本次 benchmark 是本地 fixture benchmark：

- 使用 20 个 fixture 样例任务。
- 不连接真实 Redis / Celery broker。
- 不启动独立 Celery worker 进程。
- 不访问真实外部电商网站。
- 不调用真实 LLM / embedding API。
- 不统计真实 token 成本。
- 不代表 Docker Compose 容器环境性能。

这组数据的价值是验证指标结构、统计逻辑、artifact 格式和阶段瓶颈排序，不用于声称真实线上吞吐。

### 样本结果

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

### 阶段瓶颈

| 排名 | 阶段 | 平均耗时 | 平均占比 |
| --- | --- | ---: | ---: |
| 1 | crawler | 129 ms | 38.17% |
| 2 | rag | 84 ms | 24.85% |
| 3 | report | 64 ms | 18.93% |
| 4 | agent | 50 ms | 14.79% |
| 5 | api | 14 ms | 4.14% |
| 6 | queue | 7 ms | 2.07% |

### 失败分类

| 错误码 | 次数 | 说明 |
| --- | ---: | --- |
| `ACCESS_BLOCKED` | 1 | 用 fixture 模拟采集层被拦截，后续 Day 28 可用于 retry / resume 指标 |

### 当前结论

1. 在 fixture benchmark 中，最慢阶段是 `crawler`，平均 129 ms，占平均端到端耗时 38.17%。
2. 第二瓶颈是 `rag`，平均 84 ms，占 24.85%。
3. `api` 和 `queue` 的固定开销较低，当前不是首要优化目标。
4. 本次模型调用次数和 token 总量为 0，不能用于估算真实 LLM 成本。
5. 当前失败分类只有 `ACCESS_BLOCKED`，说明 Day 28 可以优先把 retry / resume 指标接到 crawler 失败场景。

## 后续 benchmark 阶段

| 阶段 | 目标 | 前置条件 |
| --- | --- | --- |
| Docker Compose benchmark | 验证容器内 API / Worker / PostgreSQL / Redis 性能 | Docker Desktop Linux engine 可用 |
| Redis + Celery benchmark | 验证真实 broker 排队耗时和 worker 消费延迟 | 独立 worker 进程可稳定运行 |
| pgvector benchmark | 验证 PostgreSQL 原生向量排序性能 | PostgreSQL + pgvector 容器可用 |
| LLM provider benchmark | 统计真实模型调用、token、失败率和成本 | provider secret 注入和 prompt 版本冻结 |
| 并发 benchmark | 统计吞吐、P95、失败率和资源瓶颈 | 单任务主链路稳定 |

## 与其他文档关系

- 指标字段见 `llmops-metrics.md`。
- 可观测性字段见 `observability.md`。
- Day 27 计划和结果见 `../roadmap/day-27.md`。
- 后续 retry / resume 见 `../roadmap/day-28.md`。
