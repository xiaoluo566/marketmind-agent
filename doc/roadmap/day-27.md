# Day 27 - 性能与容量评估

## 当天目标

用数据了解系统瓶颈，而不是凭感觉优化。今天要收集端到端耗时、各阶段耗时、失败率和任务吞吐。

## 前置依赖

- `day-26.md` 版本流程已建立
- 阅读 `../supporting/llmops-metrics.md`
- 阅读 `../supporting/observability.md`

## 当天交付物

- benchmark 脚本
- 20 个样例任务结果
- 平均耗时统计
- 失败分类统计
- 初版性能瓶颈清单

## 实施步骤

1. 准备固定输入样例
2. 批量提交任务
3. 统计 API、queue、crawler、agent、rag、report 耗时
4. 统计 token 和模型调用次数
5. 写入 metrics summary

## 验收标准

- 知道最慢的是哪一层
- 知道失败主要来自哪一类
- 有数据可以写进简历或面试讲述

## 风险与回退

- 不要用单次任务结果代表整体表现
- 不要为了好看隐藏失败数据

## 关联文档

- 上一天：`day-26.md`
- 下一天：`day-28.md`
- 指标：`../supporting/llmops-metrics.md`
- 简历：`../supporting/resume-story.md`

## 建议提交

`perf: benchmark main execution path`

