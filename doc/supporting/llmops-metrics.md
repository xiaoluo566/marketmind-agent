# LLMOps 指标

## 目标

项目后期要能用数据证明工程化，而不是只说“用了大模型”。

## 必收集指标

- 模型名称
- 报告模型名称
- embedding 模型和维度
- prompt 版本
- 单任务 token 消耗
- 单任务模型调用次数
- 结构化输出失败次数
- 自修复成功次数
- 工具调用次数
- 工具调用失败次数
- 端到端耗时
- 报告生成耗时

## 推荐数据表

可以先放在 `agent_runs` 和 `agent_steps`，后续再拆出专门指标表。

- `model_name`
- `report_model_name`
- `embedding_model`
- `embedding_dimensions`
- `prompt_version`
- `input_tokens`
- `output_tokens`
- `total_tokens`
- `estimated_cost`
- `validation_error_count`
- `self_heal_count`
- `tool_call_count`
- `tool_failure_count`

## 建议统计

- 20 次任务成功率
- 50 次任务平均耗时
- Pydantic 拦截次数
- 自修复成功率
- 爬虫失败分类占比

## Day 12 已落地指标

Day 12 已经在 `agent_runs` 层补齐可累计指标入口：

- `validation_error_count`
- `self_heal_count`

当前统计语义：

- `validation_error_count`：JSON parse 或 Pydantic schema 校验失败次数。
- `self_heal_count`：通过 self-heal 修复后最终成功进入 schema 的次数。

注意：self-heal 调用失败或修复后仍不符合 schema，不计入 `self_heal_count`，但会保留在 guardrail error attempts 里，便于后续复盘。

## Day 14 已落地索引统计

Day 14 的 `SQLAlchemyReviewChunkStore.index_task_reviews` 返回 `ReviewChunkIndexResult`：

- `task_id`
- `review_count`
- `chunk_count`
- `embedding_model`
- `embedding_dimensions`

这些数据后续可以进入任务事件或 LLMOps 面板，用来回答：

- 当前任务实际索引了多少条评论。
- 评论被切成多少个 chunk。
- 使用了哪个 embedding 模型。
- 是否存在 embedding 维度不匹配。

当前还没有统计真实 embedding token 和成本，因为 Day 14 使用的是确定性 fake embedding provider。接入真实 provider 后，再补：

- embedding 输入字符数或 token 数。
- embedding 调用次数。
- embedding 失败次数。
- embedding 总成本估算。

## Day 34 provider 指标边界

Day34 已经把 embedding provider 接入层做成可配置架构，但还没有开始真实 provider 质量评估，因此当前指标只能分成两类：

### 架构级可统计项

- `embedding_provider_name`
- `embedding_provider_mode`：`fake` / `openai-compatible`
- `embedding_request_timeout_seconds`
- `embedding_provider_error_code`
- `embedding_provider_fallback_enabled`

### 真实运行后才能统计的项

- embedding 调用次数
- embedding 输入字符数或 token 数
- embedding 平均耗时和 P95
- embedding 失败率
- 真实 token 成本
- 真实召回质量指标

当前要特别注意：

- `EMBEDDING_PROVIDER_FALLBACK_ENABLED=true` 时，不能把 fallback 结果写成真实 provider 指标。
- `fake` provider 的结果只能用于测试、演示和 baseline，不代表真实语义效果。
- `EMBEDDING_PROVIDER_UNCONFIGURED` 应计入配置错误，而不是模型失败。

## 简历可用数据

- 平均任务耗时
- 失败恢复成功率
- 输出校验修复率
- 人工分析时间节省估算

## Day 27 已落地 benchmark 指标

Day 27 新增 `backend/app/benchmarking/main_path.py` 和 `backend/app/benchmarking/summary.py`，先把主链路 benchmark 的指标结构固化下来。

当前运行命令：

```powershell
$env:PYTHONPATH='backend'
uv run python -m app.benchmarking.main_path --iterations 20 --output-dir doc\supporting
```

当前 artifact：

- `day27-benchmark-results.json`
- `day27-benchmark-summary.json`
- `day27-benchmark-summary.md`
- `performance-benchmark.md`

当前 20 个 fixture 样例任务统计：

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

1. `crawler`：平均 129 ms。
2. `rag`：平均 84 ms。
3. `report`：平均 64 ms。

失败分类：

- `ACCESS_BLOCKED`：1 次。

注意：Day 27 benchmark 是 fixture benchmark，不调用真实 LLM / embedding API，所以模型调用次数和 token 总量必须记录为 0。后续接真实 provider 后，才允许统计真实 token、成本、模型失败率和 self-heal 成功率。

## Day 33 已补充 Retry 恢复指标口径

Day33 尚未统计真实恢复成功率，因为 Docker daemon 不可用，真实 Redis/Celery 容器链路没有完成补验。当前只固化指标口径，等待后续真实运行数据填充。

建议新增恢复类指标：

- `retry_requested_count`：用户或系统触发 retry 的次数。
- `retry_requeued_count`：成功重新入队次数，对应 `task requeued`。
- `recovery_resumed_count`：Worker 重新开始恢复执行次数，对应 `task recovery resumed`。
- `retry_queue_unavailable_count`：重试投递队列不可用次数，对应 `task retry queue unavailable`。
- `retry_recovery_success_rate`：恢复后最终完成数 / retry requested 数。
- `retry_recovery_latency_ms`：从 retry accepted 到 worker recovery resumed 的耗时。

当前 Day33 可验证事实：

- 后端单进程测试中存在 `task waiting retry`、`task requeued`、`task recovery resumed`。
- 前端展示层已将 retry/recovery 常见事件翻译为中文说明。
- mock 浏览器层可以看到 `task.retry_submitted`。

当前不能写成指标：

- 真实容器恢复成功率。
- 真实 Redis/Celery 消费耗时。
- 真实生产 retry 成本。

## 注意

没有真实跑出来的数据不要写成确定指标。简历中要写“统计得到”，而不是“理论上”。

## 与其他文档关系

- 数据字段见 `data-model.md`
- Agent 步骤见 `agent-state-machine.md`
- 简历表达见 `resume-story.md`
