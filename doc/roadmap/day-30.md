# Day 30 - 里程碑验收与发布候选

## 当天目标

Day 30 的目标是把第一阶段做成一个可展示、可复盘、可继续迭代的 release candidate。

今天不追求把所有未来功能做完，而是确认：

- 主链路能力已经有自动化测试支撑。
- README 和演示材料能指导展示。
- 指标只使用真实验证数据。
- 缺口和风险明确写出。
- 下一阶段 backlog 清楚。
- 可以创建 RC tag，但不声明 v1.0。

## 前置依赖

- `day-29.md`：README、演示脚本、简历表达和面试讲述已经整理。
- `../supporting/release-checklist.md`：发布前后检查标准。
- `../supporting/milestones-and-acceptance.md`：阶段验收标准。
- `../supporting/demo-script.md`：演示流程。
- `../supporting/rollback-runbook.md`：回退方案。

## Day 30 实际完成内容

- 新增 `tests/test_day30_release_candidate.py`。
- 新增 `doc/supporting/day30-release-candidate.md`。
- 新增 `doc/supporting/day30-metrics-summary.md`。
- 新增 `doc/supporting/day30-bug-summary.md`。
- 更新 `doc/supporting/future-iterations.md`，把第二阶段优先级具体化。
- 更新 `doc/supporting/release-checklist.md`，记录 Day 30 release candidate 状态。
- 更新 `doc/supporting/testing-strategy.md`，记录 Day 30 Release Candidate 测试边界。
- 更新 `doc/supporting/development-log.md`，记录 Day 30 开发与验证。
- 更新 `doc/supporting/interview-defense-dossier.md`，补 Day 30 里程碑验收的面试表达。
- 更新 `README.md`，加入 Day30 RC 文档入口。

## 发布候选边界

本次建议 tag：

```text
v0.1-day30-rc1
```

这是 release candidate，不是 v1.0。

原因：

- 已完成主链路工程能力、自动化测试、CI、benchmark artifact、失败任务 retry 和演示材料。
- 但真实 Docker Compose build/up 仍因 Docker Desktop daemon 不可用而未验证。
- 真实 embedding provider、真实 LLM report prompt、前端 retry 按钮、Playwright E2E、GitHub branch protection 仍未完成。

## 验收标准

- Day30 release candidate 文档存在。
- Day30 metrics summary 只使用已验证数据。
- Day30 bug summary 明确列出未解决缺口。
- future iterations 明确第二阶段优先级。
- release checklist 记录 RC tag 与边界。
- README 指向 Day30 RC 文档。
- 本地完整门禁通过。
- GitHub Actions 通过。

## 验证命令

```powershell
uv run pytest tests\test_day30_release_candidate.py
uv run pytest tests\test_day30_release_candidate.py tests\test_day29_demo_docs.py tests\test_day28_recovery.py tests\test_day27_benchmarking.py
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

## Docker 真实启动状态

本机当前 `docker info` 结果：

```text
Client: Docker version 29.3.1
Server: failed to connect to dockerDesktopLinuxEngine
```

所以 Day 30 仍然只验证 `docker compose config`，不声明真实 `docker compose build` / `docker compose up` 已完成。

## 风险与回退

- 如果完整门禁失败，不创建 RC tag。
- 如果 GitHub Actions 失败，不推 main，不声明可发布。
- 如果 demo 链路不稳定，只保留 RC tag，不声明 v1.0。
- 回退优先使用 `git revert`，不对已推送提交使用 `git reset --hard`。

## 关联文档

- 上一天：`day-29.md`
- 总计划：`30-day-master-plan.md`
- 发布候选：`../supporting/day30-release-candidate.md`
- 指标汇总：`../supporting/day30-metrics-summary.md`
- bug/缺口汇总：`../supporting/day30-bug-summary.md`
- 发布检查：`../supporting/release-checklist.md`
- 后续计划：`../supporting/future-iterations.md`

## 建议提交

```text
release: 建立 Day 30 发布候选
```
