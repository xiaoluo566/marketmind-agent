# Day 12 - 结构化输出与自愈

## 目标

降低模型输出不合规 JSON 的失败率。

## 当日任务

- 定义 Pydantic 输出模型
- 加入 Tenacity 重试
- 实现 schema 校验失败的自修复
- 记录失败样本

## 关键输出

- 输出校验层
- 重试策略
- 错误样本库

## 验收

- 非标准输出能被修正或明确失败

## Git 记录

- 建议提交：`feat: add structured output guardrails`

