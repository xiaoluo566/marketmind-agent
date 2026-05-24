# Agent 状态机

## 状态链

1. `received`
2. `classified`
3. `planned`
4. `tool_selected`
5. `tool_running`
6. `observation_saved`
7. `self_checked`
8. `reporting`
9. `completed`
10. `failed`

## 状态转移表

| 当前状态 | 触发条件 | 下一状态 | 写入内容 |
| --- | --- | --- | --- |
| `received` | 任务被 worker 拿到 | `classified` | 任务目标和输入摘要 |
| `classified` | Agent 判断任务类型 | `planned` | 任务类型、需要的工具 |
| `planned` | 选择下一步工具 | `tool_selected` | 工具名和参数草案 |
| `tool_selected` | 参数校验通过 | `tool_running` | Pending action |
| `tool_running` | 工具成功返回 | `observation_saved` | Observation 和 artifact |
| `tool_running` | 工具失败 | `failed` 或 `planned` | 错误原因和重试决策 |
| `observation_saved` | 结构化检查通过 | `self_checked` | schema 校验结果 |
| `self_checked` | 需要更多信息 | `planned` | 下一轮计划 |
| `self_checked` | 信息足够 | `reporting` | 报告生成输入 |
| `reporting` | 报告成功入库 | `completed` | report_id |

## 关键动作

- 接收用户目标并做任务分类
- 选择工具而不是直接输出结论
- 每次工具调用前写 Pending
- 每次工具调用后写 Success / Failed
- 每次 Observation 都持久化
- 在结构化输出失败时自动重试或纠错

## 记录要求

- Thought：记录决策依据
- Action：记录调用的工具和参数
- Observation：记录工具结果和关键事实
- Error：记录异常、重试和回退策略

## 断点续跑

- 必须从数据库恢复最后一个稳定步骤
- 不允许只依赖内存中的上下文
- 恢复时必须检查 schema 版本和工具版本

## 工具调用契约

每个工具必须具备：

- 输入 Pydantic schema
- 输出 Pydantic schema
- 超时设置
- 可重试标记
- 错误分类
- 结果摘要函数

## 断点续跑算法

1. 从 `agent_runs` 找到最近一次未完成 run
2. 读取最后一条 `agent_steps`
3. 如果最后一步是 `success`，从下一步继续
4. 如果最后一步是 `pending` 或 `running`，检查工具是否幂等
5. 如果工具幂等，标记旧步骤为 `failed_recovered` 后重试
6. 如果工具不幂等，创建人工确认事件

## 不要做的事

- 不要把 Agent 的全部上下文只存在 Python 变量里
- 不要直接让模型自由输出报告
- 不要让模型自己决定数据库写入
- 不要在失败后覆盖旧步骤

## 与其他文档关系

- prompt 管理见 `prompt-strategy.md`
- 数据表见 `data-model.md`
- 测试策略见 `testing-strategy.md`
