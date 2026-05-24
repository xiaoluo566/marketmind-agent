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

