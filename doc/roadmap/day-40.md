# Day 40 - 第二阶段阶段验收与发布候选

## 当天目标

Day 40 的目标是把 Day31-Day39 的第二阶段成果收口成 Phase 2 RC。它不是简单写总结，而是做阶段验收、回归门禁、缺口复盘、CI 检查、文档一致性审计和是否合并 main 的判断。

这一天的关键词是：Phase 2 RC、阶段验收、release candidate、回归门禁、诚实边界。

## 前置依赖

- `day-31.md`：中文界面基线。
- `day-32.md`：前端 retry 入口。
- `day-33.md`：retry 链路联调。
- `day-34.md`：embedding provider。
- `day-35.md`：RAG 指标。
- `day-36.md`：真实 LLM report prompt。
- `day-37.md`：Playwright E2E。
- `day-38.md`：报告导出和证据包。
- `day-39.md`：LLMOps 指标。
- `../supporting/release-checklist.md`：发布检查。
- `../supporting/phase-2-acceptance-and-risk.md`：第二阶段验收和风险。

## 当天交付物

- 新增 `doc/supporting/phase-2-release-candidate.md`。
- 新增 `doc/supporting/phase-2-bug-summary.md`。
- 新增 `doc/supporting/phase-2-metrics-summary.md`。
- 更新 README，说明 Phase 2 当前能力和边界。
- 更新 `release-checklist.md`。
- 更新 `future-iterations.md`。
- 决定是否：
  - 推送 `dev`。
  - 合并 `main`。
  - 创建 `v0.2-phase2-rc1` tag。
- 验证 GitHub branch protection / required checks 状态。如果 GitHub 权限或仓库设置不允许自动配置，要记录手动设置步骤。

## 实施步骤

1. 阶段审计：
   - 对照 Day31-Day39 文档逐项检查完成状态。
   - 检查哪些能力只完成文档，哪些已完成代码，哪些已通过 CI。
2. 测试门禁：
   - 全量 pytest。
   - coverage。
   - ruff。
   - alembic heads。
   - docker compose config。
   - frontend lint/build/audit。
   - pip-audit。
   - Playwright E2E，如果 Day37 已接入。
3. 文档门禁：
   - README 和 doc index 是否同步。
   - development-log 是否记录实际结果。
   - interview-defense-dossier 是否更新讲法。
   - testing-strategy 是否记录新增测试边界。
4. 缺口复盘：
   - 真实 compose build/up 是否完成。
   - 真实 provider 是否完成。
   - 真实 LLM prompt 是否完成。
   - E2E 是否进入 CI。
   - branch protection 是否配置。
5. 版本管理：
   - `dev` 通过 CI 后再考虑 main。
   - 不把未验证能力写进 release title。

## 测试计划

```powershell
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
uvx pip-audit
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
```

如果 Day37 已接入：

```powershell
cd frontend
npm run test:e2e
```

CI：

```powershell
git push origin dev
gh run list --branch dev --limit 5
gh run watch <run_id> --exit-status
```

## 验收标准

- Day31-Day39 的完成状态可追溯。
- 所有已完成能力有测试或明确手动验收记录。
- 未完成能力进入 `phase-2-bug-summary.md`。
- README、开发日志、面试文档、测试策略同步。
- CI 通过后才允许推 main。
- 不把 Phase 2 RC 包装成最终生产版。
- 如果创建 tag，tag 名建议 `v0.2-phase2-rc1`。

## 风险与回退

风险：

- 文档声称能力完成，但测试或 CI 无法证明。
- main 合并过早，破坏稳定分支。
- E2E 或真实 provider 不稳定导致 release 候选失真。
- branch protection 无权限自动配置。

回退：

- 如果任一核心门禁失败，不合并 main。
- 如果 E2E 不稳定，标记为 non-blocking，并记录原因。
- 如果真实 provider 未配置，只声明 provider 架构完成，不声明真实模型效果。
- 如果 branch protection 无法配置，提供手动设置截图或步骤，不假装已完成。

## 文档同步清单

- `development-log.md`：记录 Day 40 Phase 2 RC 审计结果。
- `interview-defense-dossier.md`：补充 Phase 2 总结讲法。
- `testing-strategy.md`：记录 Phase 2 RC 门禁。
- `release-checklist.md`：更新 v0.2 release candidate 检查项。
- `future-iterations.md`：把未完成项转入下一阶段。
- `README.md`：更新当前项目状态。

## 面试讲法

可以这样讲：

> Day 40 我做的是第二阶段 release candidate 收口。我不会简单说“第二阶段完成了”，而是按 Day31-Day39 的文档和测试逐项审计：哪些功能有代码、哪些有测试、哪些只完成了设计、哪些因为 Docker 或真实 provider 没有补验。这样项目的版本记录是可信的，main 分支也不会被不稳定功能污染。

如果被问“为什么又花一天做验收”，回答：

> 工程化项目不是写完功能就结束。阶段验收能把文档、测试、CI、指标、缺口和回退对齐。尤其是 Agent 项目外部依赖多，如果没有 RC 边界，很容易把 mock 能力说成真实生产能力。

## 建议提交

```text
release: 建立第二阶段发布候选
```
