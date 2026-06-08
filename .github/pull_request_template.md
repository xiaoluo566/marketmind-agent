## 变更摘要

-

## 影响范围

- [ ] Backend / API
- [ ] Worker / Celery
- [ ] Database / Migration
- [ ] Frontend
- [ ] Docker / Deployment
- [ ] Documentation only

## 验证记录

- [ ] `uv run pytest`
- [ ] `uv run pytest --cov=backend --cov-report=term-missing`
- [ ] `uv run ruff check backend tests migrations`
- [ ] `uv run alembic heads`
- [ ] `docker compose config`
- [ ] `cd frontend; npm run lint`
- [ ] `cd frontend; npm run build`
- [ ] `cd frontend; npm audit --audit-level=high`
- [ ] `uvx pip-audit`

## 回退方案

- 回退方式：
- 是否涉及数据库迁移：
- 是否需要保留或恢复 Docker volume：
- 是否影响旧任务/旧报告读取：

## 文档更新

- [ ] `doc/roadmap/day-xx.md`
- [ ] `doc/supporting/development-log.md`
- [ ] `doc/supporting/interview-defense-dossier.md`
- [ ] 相关设计 / 部署 / 测试文档
