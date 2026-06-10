# 发布检查清单

## 发布前

- 核心测试通过。
- `uv run pytest --cov=backend --cov-report=term-missing` 达到 80% coverage 门槛。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 只有预期 head。
- `docker compose config` 通过。
- `cd frontend; npm run lint` 通过。
- `cd frontend; npm run build` 通过。
- `cd frontend; npm audit --audit-level=high` 无 high 及以上漏洞。
- `uvx pip-audit` 无已知漏洞。
- `.env.example` 已更新。
- README 与文档入口已同步。
- 阶段审计文档已更新。
- 开发日志和面试文档已更新。
- 如果涉及数据库迁移，已经写明是否向后兼容和如何回退。

## Day 30 release candidate 状态

Day 30 的建议发布候选 tag 是：

```text
v0.1-day30-rc1
```

这是 release candidate，不是 v1.0。创建或推送该 tag 前，必须满足：

- Day30 release candidate 文档已更新：`day30-release-candidate.md`。
- Day30 指标汇总已更新：`day30-metrics-summary.md`。
- Day30 缺口汇总已更新：`day30-bug-summary.md`。
- `uv run pytest` 和 coverage 门禁通过。
- 后端 ruff、Alembic heads、Docker Compose config 通过。
- 前端 lint、build、audit 通过。
- `uvx pip-audit` 通过。
- GitHub Actions 新 run 通过。

当前边界必须如实记录：

- 可以声明 `docker compose config` 已验证。
- 不声明真实 `docker compose build` / `docker compose up` 已完成，除非 Docker Desktop daemon 可用后实际执行并通过。
- 不声明真实 embedding provider 调用、真实 LLM provider 调用和真实 Docker/API/provider 全链路 E2E 已完成，除非后续实际执行并通过。
- 可以声明前端 retry 按钮已在 Day32 补齐，mock 模式 Playwright E2E 主流程已在 Day37 通过，但必须注明它不是生产环境多容器 E2E。

## 发布时

- 确认当前分支和目标分支。
- 确认 GitHub 上 `dev` / `main` 状态。
- 记录提交号。
- 创建或更新回退分支，命名建议：`backup/<date>-before-<release-name>`。
- 创建 Git tag，建议格式：`v0.1-dayXX`，例如 `v0.1-day26-ci`。
- 推送 tag：

```powershell
git tag v0.1-dayXX
git push origin v0.1-dayXX
```

## 发布后

- 跑一次完整演示。
- 记录异常和修复。
- 更新 `bug-log-template.md` 或具体 bug 文档。
- 更新 `llmops-metrics.md` 或阶段指标。
- 如果发布失败，优先使用 `git revert` 回退问题提交。

## 回退优先级

1. 小范围行为错误：优先 `git revert <commit>`。
2. 多提交阶段错误：从 `backup/` 分支或上一个 tag 创建修复分支。
3. 数据库迁移错误：先评估数据兼容性，再执行 Alembic downgrade 或补偿迁移。
4. Docker 配置错误：先 `docker compose config`，再决定是否回退 compose 文件。

不建议默认使用 `git reset --hard` 处理已推送到远程的提交。已推送提交需要保留可审计历史。

## PR 检查

每个 PR 至少说明：

- 变更摘要。
- 影响范围。
- 验证命令和结果。
- 回退方案。
- 是否涉及数据库迁移。
- 是否涉及 Docker volume 或运行环境变更。
- 是否更新对应 roadmap / development log / interview dossier。

## 与其他文档关系

- 测试门槛见 `testing-strategy.md`。
- 部署方式见 `deployment.md`。
- Docker 操作见 `docker-compose-runbook.md`。
- 回退细节见 `rollback-runbook.md`。
- 里程碑验收见 `milestones-and-acceptance.md`。
- 演示流程见 `demo-script.md`。
