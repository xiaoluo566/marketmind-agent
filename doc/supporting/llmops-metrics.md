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

## 注意

没有真实跑出来的数据不要写成确定指标。简历中要写“统计得到”，而不是“理论上”。

## 与其他文档关系

- 数据字段见 `data-model.md`
- Agent 步骤见 `agent-state-machine.md`
- 简历表达见 `resume-story.md`
