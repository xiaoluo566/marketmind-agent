# 回退运行手册

## 目标

这份文档定义 MarketMind Agent 的回退策略。回退不是简单删代码，还要考虑数据库迁移、Docker volume、Worker 中的旧任务和前端是否还能读取旧报告。

## 基本原则

- 优先使用 `git revert`，保留远程分支历史。
- 不要默认使用 `git reset --hard` 回退已经推送的提交。
- 回退前先确认影响范围：代码、数据库、Docker volume、任务队列、前端构建产物。
- 高风险回退前创建 `backup/` 分支。
- 数据库迁移回退必须先确认是否会丢数据。

## 常见场景

### 单个提交引入问题

```powershell
git revert <commit_sha>
uv run pytest
uv run ruff check backend tests migrations
```

### 阶段性提交需要整体回退

```powershell
git checkout dev
git pull origin dev
git checkout -b backup/2026-06-08-before-rollback
git push -u origin backup/2026-06-08-before-rollback
```

然后从上一个稳定 tag 或 commit 创建修复分支。

### 数据库迁移回退

先查看当前 head：

```powershell
uv run alembic heads
uv run alembic current
```

如果迁移可逆并且不会丢数据：

```powershell
uv run alembic downgrade -1
```

如果会丢数据，优先写补偿迁移或导出数据，不直接 downgrade。

### Docker Compose 回退

先保留数据停止：

```powershell
docker compose down
```

切回旧版本后重新启动：

```powershell
docker compose up --build -d
```

只有确认不需要保留本地数据库和 artifact 时，才执行：

```powershell
docker compose down -v
```

## 回退后验证

```powershell
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
```

## 回退记录模板

```text
日期：
执行人：
分支：
回退原因：
影响范围：
回退方式：
涉及提交：
涉及数据库迁移：
是否保留 Docker volume：
验证命令：
验证结果：
后续修复计划：
```
