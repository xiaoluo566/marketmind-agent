# Day 13 - 短期记忆

## 当天目标

让当前任务的上下文可控增长，避免 Agent 把所有历史内容都塞进模型上下文。

## 前置依赖

- `day-12.md` 输出校验已接入
- Redis 可用
- 阅读 `../supporting/rag-memory.md`

## 当天交付物

- Redis 上下文缓存
- 滑动窗口策略
- 历史摘要策略
- 当前任务上下文读取接口

## 实施步骤

1. 为每个 task 创建短期记忆 key
2. 最近 3 轮工具调用保留详细内容
3. 更早内容压缩成摘要
4. Agent 每轮执行前加载短期记忆
5. 任务结束后把摘要写入数据库

## 验收标准

- 上下文不会无限增长
- Agent 能引用最近的工具结果
- 重启 worker 后至少能从数据库恢复关键状态

## 风险与回退

- Redis 是短期缓存，不是唯一事实来源
- 摘要不能丢掉关键证据 ID

## 关联文档

- 上一天：`day-12.md`
- 下一天：`day-14.md`
- 记忆：`../supporting/rag-memory.md`
- 数据模型：`../supporting/data-model.md`

## 建议提交

`feat: add short-term memory window`

