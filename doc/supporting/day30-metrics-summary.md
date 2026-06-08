# Day 30 指标汇总

## 文档定位

这份文档只记录已经被本地命令、测试文件或 GitHub Actions 验证过的数字。没有真实执行过的 Docker Compose build/up、真实 LLM 调用、真实 embedding 调用和真实外部网站吞吐，不在这里伪造成已完成指标。

关联文档：

- 发布候选说明：`day30-release-candidate.md`
- 缺口汇总：`day30-bug-summary.md`
- 性能基线：`day27-benchmark-summary.md`
- LLMOps 指标口径：`llmops-metrics.md`
- 测试策略：`testing-strategy.md`

## 本地质量门禁基线

截至 Day 30 release candidate 收尾，最新完整本地门禁结果为：

| 指标 | 已验证结果 | 说明 |
| --- | --- | --- |
| 全量 pytest | `167 passed` | 覆盖后端业务、Agent、RAG、报告、CI 契约、文档契约和 Day30 RC 文档测试 |
| Backend coverage | `90.79%` | 超过 `pyproject.toml` 中 `fail_under = 80` 的门槛 |
| Ruff | passed | `uv run ruff check backend tests migrations` |
| Alembic heads | passed | `0002_task_queue_id (head)` |
| Compose config | passed | 只验证配置解析，不等于真实容器启动 |
| Frontend lint/build | passed | Next.js 控制台可构建 |
| Frontend audit | passed | `npm audit --audit-level=high` 无 high 及以上漏洞 |
| Python audit | passed | `uvx pip-audit` 无已知漏洞 |

Day 29 收尾时的基线是 `162 passed`。Day30 新增 5 个 release candidate 文档测试后，最终变为 `167 passed`。

## Day27 fixture benchmark

Day27 benchmark 是 `fixture benchmark`，用于验证主链路统计模型和本地确定性样例吞吐，不代表真实外部网站、真实 Redis/Celery 集群、真实 LLM 或真实 embedding provider 的生产性能。

| 指标 | 数值 |
| --- | --- |
| 样例任务数 | `20` |
| 成功任务数 | `19` |
| 失败任务数 | `1` |
| 成功率 | `95.00%` |
| 平均端到端耗时 | `338 ms` |
| P95 端到端耗时 | `391 ms` |
| crawler 平均耗时 | `129 ms` |
| RAG 平均耗时 | `84 ms` |
| report 平均耗时 | `64 ms` |
| 模型调用次数 | `0` |
| Token 总消耗 | `0` |

## 模型与成本边界

模型调用次数：0。

当前报告生成、embedding 和 benchmark 都使用确定性实现或 fixture 输入，因此不能写成“真实 token 成本已优化”。面试中可以说：

> 我把 LLMOps 指标口径提前设计好了，但 Day30 RC 还没有接真实 provider，所以模型调用次数和 token 成本是 0。这样记录是为了避免把 fake benchmark 包装成真实线上指标。

## 可写进简历的指标

可以写：

- 构建 167 个自动化测试覆盖的工程化 Agent 主链路，backend coverage 90.79%。
- 设计 20 个 fixture 样例任务 benchmark，记录成功率 95.00%、平均耗时 338 ms、P95 391 ms。
- 将测试、coverage、ruff、Alembic、Docker Compose config、前端构建和依赖审计纳入 CI/本地门禁。

不建议写：

- “真实线上任务成功率 95%”。
- “真实外部网站 P95 391 ms”。
- “LLM token 成本已显著降低”。
- “Docker Compose 已完整启动验证”。
