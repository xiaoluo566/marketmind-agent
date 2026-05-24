# Day 03 - 数据库设计与迁移骨架

## 当天目标

把任务、Agent 状态、采集数据、评论、向量、报告和错误日志都设计成可持久化的数据结构。后续所有功能都依赖今天的数据模型。

## 前置依赖

- `day-02.md` 架构边界已确定
- 阅读 `../supporting/data-model.md`
- 阅读 `../supporting/agent-state-machine.md`

## 当天交付物

- 初版数据模型
- 状态枚举
- 主外键关系
- 索引建议
- Alembic 迁移计划

## 实施步骤

1. 定义 `tasks`、`task_events`、`agent_runs`、`agent_steps`
2. 定义 `products`、`reviews`、`review_chunks`、`reports`
3. 为所有长任务记录 `trace_id`、`status`、`created_at`、`updated_at`
4. 设计 pgvector 字段和向量索引
5. 规划 Alembic 初始迁移，不急于写复杂 repository

## 验收标准

- 每个任务能追踪状态变化
- 每个 Agent 工具调用能追踪输入和输出
- 每条评论能追踪来源页面
- 报告能关联回 task 和证据

## 风险与回退

- 不要过早设计复杂用户权限
- 如果字段不确定，先保留 JSON metadata
- 数据库变更要写入 `../supporting/change-management.md`

## 关联文档

- 上一天：`day-02.md`
- 下一天：`day-04.md`
- 数据模型：`../supporting/data-model.md`
- API 契约：`../supporting/api-contract.md`

## 建议提交

`feat: design initial data model`

