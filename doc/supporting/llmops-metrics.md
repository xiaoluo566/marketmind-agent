# LLMOps 指标

## 目标

项目后期要能用数据证明工程化，而不是只说“用了大模型”。

## 必收集指标

- 模型名称
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

## 简历可用数据

- 平均任务耗时
- 失败恢复成功率
- 输出校验修复率
- 人工分析时间节省估算

## 注意

没有真实跑出来的数据不要写成确定指标。简历中要写“统计得到”，而不是“理论上”。

## 与其他文档关系

- 数据字段见 `data-model.md`
- Agent 步骤见 `agent-state-machine.md`
- 简历表达见 `resume-story.md`
