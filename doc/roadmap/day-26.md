# Day 26 - CI 与版本回退策略

## 当天目标

Day 26 的目标是把 Day 23 到 Day 25 已经形成的本地质量门禁固化到 GitHub Actions，并把“怎么合入、怎么发版、怎么回退”写成可执行流程。

今天不继续新增业务能力，也不把 Docker Compose 真正跑起来作为 CI 强制要求。原因是 Day 25 已经确认本机 Docker Desktop Linux engine 未运行，真实镜像构建和 `docker compose up` 需要单独在 daemon 可用时验证；Day 26 先解决的是“每次提交是否能自动验证代码、测试、迁移、前端构建、安全审计和 compose 配置没有漂移”。

## 前置依赖

- `day-23.md`：已经建立 pytest、coverage fail-under 80、状态策略和 schema 契约测试。
- `day-24.md`：已经建立主链路集成回归样例。
- `day-25.md`：已经建立 Docker Compose 服务拓扑、Dockerfile、`.dockerignore` 和 compose 契约测试。
- `../supporting/testing-strategy.md`：定义测试分层和 Day 23 - Day 25 的测试边界。
- `../supporting/release-checklist.md`：定义发版前后检查项。
- `../supporting/change-management.md`：定义分支、提交和风险记录原则。

## 当天交付物

- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `tests/test_day26_ci_contract.py`
- `doc/supporting/release-checklist.md`
- `doc/supporting/rollback-runbook.md`
- `doc/supporting/testing-strategy.md` Day 26 测试边界补充
- `doc/supporting/development-log.md` Day 26 开发记录
- `doc/supporting/interview-defense-dossier.md` Day 26 面试表达补充

## 实际完成内容

### 1. GitHub Actions CI

新增 `.github/workflows/ci.yml`，触发条件为：

- `pull_request` 到 `main` / `dev`
- `push` 到 `main` / `dev`

CI 分成两个 job：

| Job | 运行环境 | 核心命令 | 目的 |
| --- | --- | --- | --- |
| `backend` | Ubuntu + Python 3.12 + uv | `uv sync --frozen`、`uv run ruff check backend tests migrations`、`uv run pytest --cov=backend --cov-report=term-missing`、`uv run alembic heads`、`docker compose config`、`uvx pip-audit` | 锁住后端测试、覆盖率、迁移、compose 配置和 Python 依赖安全 |
| `frontend` | Ubuntu + Node 22 | `npm ci`、`npm run lint`、`npm run build`、`npm audit --audit-level=high` | 锁住前端依赖、lint、构建和高危漏洞 |

CI 中使用 `concurrency` 取消同一分支上过时的旧运行，避免频繁 push 时浪费资源。

### 2. CI 边界

Day 26 CI 明确不执行：

```powershell
docker compose build
docker compose up
```

原因：

- CI 的第一阶段目标是稳定、快速、可重复的质量门禁。
- `docker compose config` 已经可以检查 YAML、变量插值、服务依赖和配置解析。
- 真实容器构建和服务健康检查会显著增加耗时，并且需要额外处理镜像缓存、Playwright 浏览器依赖、数据库 readiness 和 worker 消费样例任务。
- Day 25 本机已经记录 Docker daemon 未运行，不能把尚未完成的真实 build/up 伪装成已经完成。

后续如果要把真实 Compose E2E 放入 CI，应独立成 `compose-e2e` job，并设置明确超时、日志上传和失败保留 artifact。

### 3. PR 模板

新增 `.github/pull_request_template.md`，要求每个 PR 至少说明：

- 变更摘要
- 影响范围
- 验证记录
- 回退方案
- 是否涉及数据库迁移
- 是否需要保留或恢复 Docker volume
- 是否影响旧任务或旧报告读取
- 是否更新 roadmap / development log / interview dossier

这样做的目的不是增加形式，而是让每次合入都能回答三个问题：

1. 这次改了什么？
2. 怎么证明它没有破坏主链路？
3. 如果出问题怎么撤？

### 4. 发布与回退文档

重写并补充 `doc/supporting/release-checklist.md`，把发布前检查项固定为：

- backend pytest
- coverage fail-under 80
- ruff
- Alembic heads
- `docker compose config`
- frontend lint/build
- npm audit
- pip-audit
- 文档同步
- 数据库迁移兼容性说明

新增 `doc/supporting/rollback-runbook.md`，明确回退原则：

- 已推送提交优先使用 `git revert`，不要默认 `git reset --hard`。
- 高风险回退前创建 `backup/` 分支。
- 数据库迁移回退必须先评估是否丢数据。
- Docker Compose 回退默认保留 volume，只有确认不需要本地数据时才 `docker compose down -v`。

### 5. CI 契约测试

新增 `tests/test_day26_ci_contract.py`，用测试锁住 Day 26 工程流程：

- CI 必须包含 backend/frontend 两套质量门禁。
- CI 必须跑 coverage、ruff、alembic heads、compose config、安全审计、前端 lint/build。
- CI 不能包含 `docker compose up` 或 `docker compose build`。
- PR 模板必须要求验证记录和回退方案。
- release checklist 必须包含 tag、backup、revert、compose 和 coverage 关键项。
- rollback runbook 必须定义 Git、数据库迁移和 Docker Compose 回退。
- testing strategy 与 development log 必须记录 Day 26。

## 当天为什么这样选

### 为什么 Day 26 先做 CI，而不是继续做性能 benchmark？

Day 27 的 benchmark 依赖稳定的质量门禁。如果没有 CI，后续性能数据即使跑出来，也很难保证每次改动后代码仍然满足基础测试、覆盖率、构建和安全要求。Day 26 先把“能不能合入”自动化，Day 27 再谈“跑得快不快”更合理。

### 为什么 CI 不直接跑完整 Docker Compose？

因为当前项目还没有完成真实容器 build/up 验证，Day 25 已经把这个事实写入运行手册。CI 里先跑 `docker compose config` 是为了验证配置契约，而不是假装已经完成真实基础设施联调。把还不稳定的 heavy E2E 放进早期 CI，只会让失败原因混杂在 Docker daemon、镜像构建、数据库 readiness、Playwright 依赖和业务逻辑之间。

### 为什么要把回退写成文档和 PR 模板？

工程化项目不能只考虑“怎么开发”，还要考虑“怎么撤回”。尤其这个项目有数据库迁移、Docker volume、Worker 长任务和历史报告。如果回退只靠临时记忆，很容易误删数据或破坏远程历史。PR 模板和回退手册让每次变更都提前思考影响范围和恢复路径。

## 验收标准

| 标准 | 当前结果 |
| --- | --- |
| CI workflow 存在 | 已新增 `.github/workflows/ci.yml` |
| backend job 覆盖 lint/test/coverage/migration/compose/security | 已覆盖 |
| frontend job 覆盖 install/lint/build/security | 已覆盖 |
| CI 不强制 compose build/up | 已通过契约测试约束 |
| PR 模板要求验证和回退 | 已新增 |
| 发布清单包含 tag、backup 和 revert | 已补充 |
| 回退手册覆盖 Git、数据库和 Docker | 已新增 |
| Day26 文档同步 | 已更新 roadmap、testing strategy、development log、interview dossier |

## 验证命令

```powershell
uv run pytest tests\test_day26_ci_contract.py
uv run pytest tests\test_day26_ci_contract.py tests\test_day25_compose_contract.py tests\test_day24_integration_flow.py
docker compose config
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

当前验证结果：

```text
Day 26 CI contract tests: 4 passed
Day 24 - Day 26 targeted tests: 9 passed
docker compose config: passed
uv run pytest: 145 passed
uv run pytest --cov=backend --cov-report=term-missing: 145 passed, backend coverage 90.86%, fail-under 80 reached
uv run ruff check backend tests migrations: All checks passed
uv run alembic heads: 0002_task_queue_id (head)
frontend npm run lint: passed
frontend npm run build: passed
frontend npm audit --audit-level=high: found 0 vulnerabilities
uvx pip-audit: No known vulnerabilities found
```

GitHub Actions 远程验证：

```text
run id: 27123022288
branch: dev
trigger: push
result: success
backend quality gate: passed
frontend quality gate: passed
```

## 遗留问题

- 还没有把真实 `docker compose build` / `docker compose up` 放入 CI 或本地补验。
- 还没有 release tag，Day 30 里程碑发布时再打正式 tag。
- `uvx pip-audit` 在 CI 中依赖网络，后续如果 GitHub Actions 网络不稳定，可以考虑固定 audit 环境或改成定期安全扫描 job。
- PR 模板目前是流程约束，还没有 branch protection rule；后续可以在 GitHub 仓库设置中强制 PR 和 required status checks。

## 关联文档

- 上一天：`day-25.md`
- 下一天：`day-27.md`
- 测试策略：`../supporting/testing-strategy.md`
- 发版清单：`../supporting/release-checklist.md`
- 回退手册：`../supporting/rollback-runbook.md`
- 变更管理：`../supporting/change-management.md`
- 部署运行：`../supporting/docker-compose-runbook.md`

## 建议提交

```text
ci: 建立 Day 26 质量门禁和回退流程
```
