# 简历表达

## 项目描述建议

把项目描述成“面向电商运营的评论洞察 Agent 系统”，不要写成普通爬虫，也不要写成纯聊天机器人，更不要写成成熟卖家工具替代品。简历重点要落在工程链路、长任务处理、状态持久化、RAG 证据链和稳定性设计上。

## 一句话版本

设计并实现面向电商运营的评论洞察 Agent 系统，基于 FastAPI、Celery、Redis、PostgreSQL/pgvector、Playwright 和 Next.js 构建异步采集、Agent 状态持久化、评论语义检索和带证据链的结构化报告生成闭环。

## 可强调的技术点

- FastAPI 异步 API 网关
- Celery + Redis 长任务解耦
- PostgreSQL 状态持久化
- Playwright 异步采集
- pgvector 语义检索
- Agent 状态机与断点续跑
- Pydantic 结构化校验
- Docker Compose 一键部署

## 简历 bullet 初稿

- 基于 FastAPI + Celery + Redis 设计长任务异步调度架构，将多分钟采集和 LLM 分析任务从 HTTP 请求中解耦，API 提交后立即返回 `task_id`，前端通过任务事件流查看进度。
- 设计 PostgreSQL 状态持久化模型，将 Agent 的 Thought、Action、Observation 和工具执行结果逐步落库，支持失败定位、执行回放和从最近 Observation 断点恢复。
- 基于 Playwright Async 实现竞品页面采集与证据保存，保存页面截图、原始 HTML、抽取文本和来源 URL，提升报告结论可追溯性。
- 使用 pgvector 构建评论 RAG 检索链路，对差评进行清洗、切片、Embedding 和语义召回，为“质量差、物流慢、售后差”等维度提供证据片段。
- 使用 Pydantic + Tenacity 构建结构化输出校验和自修复机制，记录 JSON 解析失败、重试次数和修复成功率，提升报告生成稳定性。

## 等项目完成后要补的数据

- 跑了多少个样例任务
- 平均端到端耗时
- Agent 平均工具调用次数
- Pydantic 拦截次数
- 自修复成功率
- 爬虫失败分类占比

## 建议写法

- 用动词开头
- 用结果说明技术
- 用数据证明工程化
- 不写没有统计过的绝对指标
- 不把爬虫能力夸成“全网稳定采集”
- 不把项目夸成“替代成熟卖家工具”

## 与其他文档关系

- 指标来源见 `llmops-metrics.md`
- 市场定位见 `market-positioning.md`
- 演示流程见 `demo-script.md`
- 面试展开见 `interview-story.md`
