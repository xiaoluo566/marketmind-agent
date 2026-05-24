# Day 11 - ReAct 循环与状态落库

## 目标

让 Agent 具备真正的“思考-行动-观察”闭环。

## 当日任务

- 实现循环驱动
- 写入 Thought / Action / Observation
- Tool 调用前写 Pending
- Tool 调用后更新状态

## 关键输出

- Agent state machine
- 运行日志表
- 断点续跑基础

## 验收

- 每一步都能从数据库还原

## Git 记录

- 建议提交：`feat: persist agent reasoning steps`

