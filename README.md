# MarketMind Agent

电商评论洞察与证据链报告 Agent。

这个仓库用于开发 FastAPI + Celery + PostgreSQL/pgvector + Playwright + Next.js 的电商评论洞察 Agent 系统。

## 当前状态

- `doc/`：30 天开发计划 + 横向设计文档
- `backend/`：FastAPI 后端、Celery worker、SQLAlchemy 持久化、Playwright 采集、Agent 状态机、RAG 和报告模块
- `frontend/`：Next.js 控制台，已接入真实任务提交、任务详情轮询、历史任务、历史报告、报告详情和报告证据链
- `stitch_marketmind_control_center/`：本地 Stitch 原始设计导出，已被 `.gitignore` 忽略，只作为可选视觉参考
- 本地 Git：已初始化
- GitHub：私有仓库已创建并已推送初始版本
- 分支策略：`main` 保持稳定演示版本，`dev` 用于 Day 2 以后日常开发

## 阅读顺序

1. [doc/README.md](doc/README.md)
2. [doc/supporting/project-charter.md](doc/supporting/project-charter.md)
3. [doc/supporting/dependency-map.md](doc/supporting/dependency-map.md)
4. [doc/supporting/architecture.md](doc/supporting/architecture.md)
5. [doc/supporting/data-model.md](doc/supporting/data-model.md)
6. [doc/roadmap/30-day-master-plan.md](doc/roadmap/30-day-master-plan.md)

## 项目定位

这不是一个单纯的爬虫项目，也不是一个只会聊天的 Agent demo。它要做的是把“采集、分析、证据链、报告、回退、复盘”串成一个能持续迭代的工程系统。

更具体地说，它面向电商运营场景，重点解决评论洞察、证据链报告和长任务可追踪，而不是试图替代成熟卖家工具。

## 当前阶段

当前已完成 Day 1-25 的阶段性开发，并完成一次推主分支前审计。系统已经具备：

- FastAPI 统一 API envelope 和 trace ID。
- Celery + Redis 长任务分发与任务状态缓存。
- PostgreSQL / SQLAlchemy 任务、事件、Agent step、评论、review chunk、报告和 artifact 持久化。
- Playwright 最小采集链路和 HTML artifact 保存。
- Agent 工具 schema、工具注册、最小 ReAct 状态机和 Agent step 落库。
- Pydantic Guardrails、结构化输出修复和自愈统计入口。
- 短期记忆滑动窗口、评论清洗切片、deterministic embedding、review chunk 检索。
- `search_reviews_tool`、结构化报告生成、证据链回查和风险/机会评分。
- Next.js 真实任务提交、任务详情轮询、Agent step 摘要、历史任务、历史报告、报告详情和报告 evidence chain 展示。
- 结构化错误日志、`error_logs` 持久化、观测错误查询 API。
- pytest 快速测试、coverage fail-under 80 门禁、状态转换策略、核心 schema 契约测试和主链路集成回归样例。
- Docker Compose 服务拓扑、后端/前端 Dockerfile、迁移服务、健康检查、数据卷和 compose 契约测试。

尚未完成的能力包括任务重试、全局 evidence 检索接口、真实 embedding provider、pgvector 原生排序、真实 LLM report prompt、Docker Desktop daemon 启动后的真实镜像 build / compose up 验证和 Playwright E2E。

## 验证命令

```powershell
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
uv run pytest tests\test_day25_compose_contract.py
docker compose config
cd frontend
npm run lint
npm run build
```

## 开发原则

- 先做可跑通的闭环，再做规模化扩展
- 先保证可观测和可回退，再优化性能
- 所有长任务必须有状态持久化和失败恢复
- 所有 Agent 输出必须经过结构化校验
- 所有新功能都要能落到对应的文档和验收标准上

## 版本策略

- `main`：可演示、可回退、可打标签的稳定版本
- `dev`：日常开发汇总分支
- `feature/*`：短周期功能分支
- 每个里程碑都保留 Git tag 和 GitHub 版本记录
