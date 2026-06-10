# 开发流程

## Day33+ Spec Kit SDD 固定流程

从 Day33 开始，本项目正式接入 GitHub Spec Kit。后续开发不再只按
`day-xx.md -> 写代码 -> 补文档` 的方式推进，而是采用下面的固定顺序：

```text
Spec Kit SDD -> tdd-workflow -> 代码实现 -> verification-loop -> 开发日志/面试文档/测试文档回填
```

这个顺序的目的不是增加形式，而是把需求、接口契约、验收标准、测试和面试讲述绑定在同一条链路里。项目已经进入第二阶段，后续会涉及真实 provider、E2E、导出、LLMOps 和阶段发布，单靠临时口头需求很容易造成文档、代码、测试和演示口径不一致。

### 1. Spec Kit SDD

每天开始开发前，先读当天 `doc/roadmap/day-xx.md` 和相关 supporting 文档，再使用 Spec Kit 检查或创建规格。

推荐顺序：

1. `$speckit-specify`：写清楚用户目标、功能范围、非目标、输入输出、错误场景和验收标准。
2. `$speckit-plan`：把规格转成实现计划，明确影响模块、数据模型、API、前端、测试和回退。
3. `$speckit-tasks`：拆成可执行任务，避免一次性大改。
4. `$speckit-clarify`：当需求存在歧义时先澄清，不带着模糊前提写代码。
5. `$speckit-analyze` 或 `$speckit-checklist`：当功能跨前端、后端、数据库、Agent、RAG 或部署时，用于检查规格、计划、任务之间是否一致。

Spec Kit 产物默认进入 `specs/`，并应和当天 roadmap 互相引用。roadmap 仍然是 30+ 天计划的时间线，Spec Kit 负责把单个功能变成可执行规格。

### 2. tdd-workflow

规格明确后，先写失败测试，再实现功能。

要求：

- 新后端能力先写 pytest 或契约测试。
- 新前端行为先写源码契约测试、组件行为测试或 E2E 测试。
- 修改 API、状态机、数据模型、报告 schema 或恢复流程时，测试必须覆盖错误路径。
- 必须确认测试先失败，再写实现让它通过。

### 3. 代码实现

实现阶段遵守现有工程边界：

- 优先沿用已有 FastAPI、SQLAlchemy、Celery、Redis、Next.js、Pydantic、pytest 和前端 API client 模式。
- 不为了单个功能引入重型新依赖。
- 不翻译 `task_id`、`trace_id`、API 字段、状态枚举和 provider 名。
- 中文 UI 变更必须符合 `frontend-localization-contract.md`。
- mock / fixture / fake provider 只能用于测试和演示，不能写成真实线上指标。

### 4. verification-loop

实现后按改动范围运行验证。

常用门禁：

```powershell
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
uvx pip-audit
git diff --check
```

如果是用户可见前端功能，还需要浏览器或 E2E 验收。没有真实验证的能力，只能记录为 mock / fixture / planned，不能写成已生产可用。

### 5. 文档回填

每天收尾必须更新：

- `doc/roadmap/day-xx.md`：当天实际完成、验证结果、遗留问题。
- `doc/supporting/development-log.md`：开发过程、为什么这样选、问题和修复。
- `doc/supporting/interview-defense-dossier.md`：面试讲法、技术选择和追问回答。
- `doc/supporting/testing-strategy.md`：新增测试边界、覆盖范围和不覆盖内容。

按影响范围额外更新：

- API：`api-contract.md`
- 数据表：`data-model.md`
- Agent 状态机：`agent-state-machine.md`
- RAG / embedding：`rag-memory.md`、`model-and-data-decisions.md`
- Prompt：`prompt-strategy.md`
- 前端中文术语：`frontend-localization-contract.md`
- 部署或 CI：`deployment.md`、`release-checklist.md`
- 风险和开放问题：`risk-register.md`、`open-questions.md`

## Spec Kit 接入记录

接入命令：

```powershell
specify init . --force --integration codex --integration-options="--skills" --script ps
```

接入结果：

- `.specify/`：Spec Kit 模板、PowerShell 脚本、constitution、workflow 和 Codex integration metadata。
- `.agents/skills/speckit-*`：Codex 可用的 Spec Kit skills，包括 specify、plan、tasks、implement、analyze、checklist、clarify、constitution、agent-context-update、taskstoissues。
- `AGENTS.md`：仓库级 Codex 指令，声明 Day33+ 固定流程和项目边界。
- `.specify/memory/constitution.md`：本项目 Day33+ 的 SDD 宪法。

## 每日流程

1. 先读当天 `doc/roadmap/day-xx.md`。
2. 确认输入依赖是否满足。
3. 用 Spec Kit / SDD 写或检查需求规格、接口契约、验收标准。
4. 创建小范围任务分支，或在用户明确要求时继续使用 `dev`。
5. 用 TDD 先写失败测试。
6. 实现最小功能。
7. 运行 verification-loop。
8. 更新 roadmap、development-log、interview-defense-dossier、testing-strategy。
9. 按需更新 bug / research / open questions / risk 文档。
10. 提交小步 commit。

## 开工前检查

- 当前分支是否正确
- 工作区是否干净
- 前一天的验收项是否完成
- 当天文档的前置文档是否读过
- 是否需要新增数据库迁移
- 是否需要新增测试数据

## 分支策略

- `main`：稳定版本，只合入可演示状态
- `dev`：日常集成分支
- `feature/day-xx-topic`：当天功能分支
- `hotfix/topic`：修复已知问题

## 提交建议

- `docs:` 文档
- `feat:` 新功能
- `fix:` 修复
- `test:` 测试
- `refactor:` 重构
- `chore:` 工程配置
- `perf:` 性能优化

## 回退要求

- 每天至少一个可回退点
- 每周打一个里程碑 tag
- 数据库迁移必须能说明回滚方式

## 文档更新规则

- 改 API 前先改 `api-contract.md`
- 改数据表前先改 `data-model.md`
- 改 Agent 流程前先改 `agent-state-machine.md`
- 改 prompt 前先改 `prompt-strategy.md`
- 改部署方式前先改 `deployment.md`
- 每天收尾前更新 `development-log.md`

## 与其他文档关系

- 里程碑见 `milestones-and-acceptance.md`
- 开发记录见 `development-log.md`
- 发版见 `release-checklist.md`
- 风险见 `risk-register.md`
