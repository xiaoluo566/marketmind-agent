# Day 37 - Playwright E2E 主链路

## 当天目标

Day 37 的目标是补齐真实浏览器层面的 Playwright E2E 主链路，覆盖从新建调研到任务详情、报告详情、证据链和失败重试的核心路径。此前多数验证停留在 Python 契约测试、Next.js build 和 agent-browser-cli 文本扫描，Day 37 要建立可在 CI 中运行的浏览器回归基础。

这一天不追求覆盖所有 UI 细节，而是先让最关键路径稳定可测。

## 前置依赖

- `day-19.md`：Next.js 任务提交和真实 API client。
- `day-20.md`：任务详情轮询和 Agent steps。
- `day-21.md`：历史任务和报告 API。
- `day-31.md`：中文界面基线。
- `day-32.md`：前端 retry 按钮。
- `day-33.md`：重试链路联调。
- `../supporting/testing-strategy.md`：E2E 策略。
- `../supporting/phase-2-acceptance-and-risk.md`：CI 和回退边界。

## 当天交付物

- 新增 Playwright 配置或补齐现有配置。
- 新增 E2E 测试：
  - 首页可打开。
  - 新建调研页可填写表单。
  - 任务列表可查看任务。
  - 失败任务详情可看到 `重试任务`。
  - 报告列表可进入报告详情。
  - 证据链页可看到评论语义检索。
- E2E 默认使用 mock dev server，避免依赖 Docker daemon。
- 产物保存：
  - screenshot。
  - trace。
  - HTML report。
- CI 可选接入，如果耗时可先作为手动 gate。

## 实施步骤

1. 先写 E2E 文档契约测试：
   - 确认 package scripts 包含 `test:e2e` 或等价命令。
   - 确认 Playwright 配置指向 mock 环境。
2. 安装/配置 Playwright：
   - 如果已有依赖，复用。
   - 如果新增依赖，更新 lockfile，并记录原因。
3. 编写 Page Object 或轻量 helper：
   - `DashboardPage`。
   - `NewResearchPage`。
   - `TaskDetailPage`。
   - `ReportPage`。
4. 编写第一批 E2E：
   - 用中文 text locator，不依赖英文。
   - 不依赖随机网络。
   - 不依赖真实 LLM provider。
5. 本地运行 E2E。
6. 根据稳定性决定是否纳入 CI required gate。

## 测试计划

```powershell
cd frontend
npm run lint
npm run build
npm run test:e2e
```

后端不一定参与 E2E。如果需要真实 API 模式，必须先确认后端和 Redis / Celery 可用，再单独记录。

同时运行：

```powershell
uv run pytest tests\test_frontend_localization_contract.py
uv run pytest tests\test_frontend_retry_contract.py
```

## 验收标准

- Playwright E2E 能在本地稳定运行。
- 至少覆盖首页、新建调研、任务、报告、证据链、retry 入口。
- E2E 使用中文可见文本做断言。
- E2E 不依赖真实外部模型。
- 失败时能生成 screenshot / trace。
- 如果没有接入 CI，必须在文档中说明原因和接入计划。

## 风险与回退

风险：

- E2E 因异步轮询不稳定。
- 真实 API / mock 模式环境变量在 Next.js 构建时被内联。
- Windows 本地浏览器依赖安装失败。
- CI 运行时间过长。

回退：

- 首版 E2E 只跑 mock 模式。
- 不把 E2E 立刻设为 required check，先观察稳定性。
- 对轮询页面使用明确等待条件，不用固定 sleep。

## 文档同步清单

- `testing-strategy.md`：新增 Playwright E2E 边界、命令和产物。
- `development-log.md`：记录 Day 37 本地和 CI 验证结果。
- `interview-defense-dossier.md`：补充“如何证明前端真的可用”的回答。
- `phase-2-acceptance-and-risk.md`：记录 E2E 是否纳入 required check。
- `dev-workflow.md`：如果新增 npm script，同步开发命令。

## 面试讲法

可以这样讲：

> Day 37 我给项目补了 Playwright E2E。之前 API、状态机、RAG、报告都有测试，但浏览器端只能靠手动打开。E2E 覆盖中文首页、新建调研、任务详情、报告详情、证据链和失败重试入口，能证明这个系统不只是后端能跑，用户路径也能回归。

如果被问“为什么 E2E 先用 mock 模式”，回答：

> 因为 E2E 首要目标是稳定验证前端路径，不应该同时依赖 Docker daemon、Redis、Celery 和模型 provider。真实 API E2E 可以作为第二层验收，先把浏览器路径稳定下来更合理。

## 建议提交

```text
test: 增加 Playwright E2E 主链路
```
