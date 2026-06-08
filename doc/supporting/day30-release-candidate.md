# Day 30 Release Candidate

## 结论

本次 Day 30 release candidate 建议标记为：

```text
v0.1-day30-rc1
```

这是第一阶段可展示候选版本，不声明 v1.0。

## release candidate 范围

本 RC 覆盖：

- FastAPI API gateway。
- Celery + Redis 长任务分发。
- PostgreSQL / SQLAlchemy 持久化模型。
- Playwright 最小采集和 artifact。
- Agent 工具 schema、最小 ReAct 状态机和 Agent steps。
- Pydantic Guardrails 和 self-heal 指标入口。
- 评论清洗、切片、deterministic embedding 和 review chunk 检索。
- `search_reviews_tool`。
- 结构化报告、证据链回查和风险机会评分。
- Next.js 控制台真实 API 接入。
- 结构化错误日志和观测错误查询 API。
- Docker Compose 拓扑和 `docker compose config` 验证。
- GitHub Actions backend / frontend quality gates。
- Day27 fixture benchmark。
- Day28 任务级失败 retry。
- Day29 README、演示脚本、简历表达和面试讲述材料。

## 不进入 RC 范围

本 RC 不包含：

- 真实 Docker Compose build/up 验证。
- 前端 retry 按钮。
- 真实 embedding provider。
- pgvector 原生 SQL 排序。
- 真实 LLM report prompt。
- Playwright E2E。
- GitHub branch protection required checks。
- 精确 Agent step replay。
- 全网稳定采集。

## Docker Desktop daemon 状态

Day 30 已执行 `docker info`。

结果：

```text
Client: Docker version 29.3.1
Server: failed to connect to dockerDesktopLinuxEngine
```

因此本 RC 只声明 `docker compose config` 已验证，不声明真实 `docker compose build` 或 `docker compose up` 已完成。

## GitHub Actions

Day 30 最新远程 GitHub Actions 已通过：

```text
run id: 27138404103
backend quality gate: success
frontend quality gate: success
```

Day 30 提交推送后已经观察新的 GitHub Actions run。backend 和 frontend quality gates 都通过，`v0.1-day30-rc1` 可以作为有效 RC tag。

## 验证要求

创建 tag 前必须通过：

- `uv run pytest`
- `uv run pytest --cov=backend --cov-report=term-missing`
- `uv run ruff check backend tests migrations`
- `uv run alembic heads`
- `docker compose config`
- `cd frontend; npm run lint`
- `cd frontend; npm run build`
- `cd frontend; npm audit --audit-level=high`
- `uvx pip-audit`

## 回退路径

如果 RC 后发现问题：

1. 优先使用 `git revert <commit_sha>`。
2. 如需回到上一个稳定阶段，基于 Day29 提交 `351bdac` 创建修复分支。
3. 如果 tag 已推送且不应继续使用，新增修复 tag，不强删远端 tag，除非明确确认没有其他人依赖。
4. 数据库迁移回退前先检查 `uv run alembic current` 和数据兼容性。

## 面试讲法

可以这样讲：

> Day 30 我没有把项目包装成 v1.0，而是做 release candidate。因为核心工程链路、测试、CI、benchmark 和演示材料已经具备展示条件，但真实 compose up、真实 provider 和前端 retry 按钮还没完成。把它标成 `v0.1-day30-rc1` 更符合真实工程习惯。
