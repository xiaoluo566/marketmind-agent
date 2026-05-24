# Day 05 - Celery 与 Redis 基础接入

## 目标

让长任务从 API 中解耦。

## 当日任务

- 接入 Celery
- 接入 Redis
- 实现最小异步任务
- 返回 `task_id`

## 关键输出

- 任务提交接口
- 异步执行骨架
- 任务状态查询原型

## 验收

- API 不阻塞
- Worker 能消费任务

## Git 记录

- 建议提交：`feat: add celery task pipeline`

