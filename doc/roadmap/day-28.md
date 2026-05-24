# Day 28 - 失败恢复与重试策略

## 当天目标

让系统在可恢复失败后能继续运行，而不是只能从头重跑。今天重点是重试策略、断点续跑和人工兜底。

## 前置依赖

- `day-27.md` 已有失败统计
- 阅读 `../supporting/agent-state-machine.md`
- 阅读 `../supporting/risk-register.md`

## 当天交付物

- 失败分类表
- 重试次数上限
- 断点恢复逻辑
- 手工导入恢复路径
- 重试 API 或操作入口

## 实施步骤

1. 区分可重试和不可重试错误
2. 为 Celery 任务配置退避重试
3. 为 Agent step 设计恢复算法
4. 失败后从最后成功 Observation 继续
5. 在前端显示可执行的重试动作

## 验收标准

- 爬虫超时可重试
- schema 错误可 self-heal
- 不可恢复错误能明确提示
- 旧失败记录不会被覆盖

## 风险与回退

- 不要无限重试
- 不要对非幂等工具盲目重放
- 恢复前要检查工具版本和 schema 版本

## 关联文档

- 上一天：`day-27.md`
- 下一天：`day-29.md`
- 状态机：`../supporting/agent-state-machine.md`
- 风险：`../supporting/risk-register.md`

## 建议提交

`feat: add recovery and retry policies`

