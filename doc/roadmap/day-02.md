# Day 02 - 架构总图与技术选型冻结

## 当天目标

把系统拆成清晰的逻辑层，确定第一版技术栈和暂不做的内容。今天的重点不是炫技术，而是让后续每个模块都有明确边界。

## 前置依赖

- `day-01.md` 已完成
- 阅读 `../supporting/project-charter.md`
- 阅读 `../supporting/tech-stack-decisions.md`

## 当天交付物

- 架构分层说明
- 技术选型说明
- 第一版部署拓扑
- 后续可拆分模块列表

## 实施步骤

1. 确定第一版采用“模块化单体 + Celery worker”的方式
2. 明确 API、Worker、Agent、Crawler、RAG、Report、Storage 的边界
3. 写清楚 FastAPI、Celery、Redis、PostgreSQL、Playwright、pgvector 的职责
4. 列出不立即引入的技术，例如 Kafka、Kubernetes、Milvus
5. 将架构决策写入 `../supporting/architecture.md`

## 验收标准

- 能画出请求从前端到报告生成的完整链路
- 能解释为什么第一版不拆复杂微服务
- 能解释每个技术栈解决的具体问题

## 风险与回退

- 如果发现某项技术会拖慢 30 天交付，放入 `../supporting/future-iterations.md`
- 如果架构争议影响实现，放入 `../supporting/open-questions.md`

## 关联文档

- 上一天：`day-01.md`
- 下一天：`day-03.md`
- 架构：`../supporting/architecture.md`
- 技术选型：`../supporting/tech-stack-decisions.md`

## 建议提交

`docs: freeze architecture and stack decisions`

