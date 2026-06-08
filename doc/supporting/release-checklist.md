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
