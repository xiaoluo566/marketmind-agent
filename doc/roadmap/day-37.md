# Day 37 - Playwright E2E 主链路

## 当天目标

Day37 的目标是补齐真实浏览器层面的 Playwright E2E 主链路，覆盖从新建调研到任务详情、报告详情、证据链和失败重试的核心路径。此前多数验证停留在 Python 契约测试、Next.js build 和手动浏览器检查，Day37 要建立一个可以在本地稳定运行、后续可以接入 CI 的浏览器回归基础。

这一天不追求覆盖所有 UI 细节，而是先让最关键路径可测：工作台 -> 新建调研 -> 任务详情 -> 失败任务 retry -> 报告详情 -> 证据链。

## SDD 检查记录

Day37 的规格边界是“浏览器主链路回归”，不是“真实后端全链路压测”。

用户目标：

- 运营用户可以通过真实浏览器完成核心页面跳转和操作。
- 开发者可以用一条命令验证中文控制台主链路没有断。
- 失败时能拿到 Playwright trace、screenshot、video 和 HTML report。

功能范围：

- 首页工作台。
- `新建调研` 表单。
- 任务详情页和 Agent 步骤。
- 失败任务 `重试任务`。
- 报告列表和报告详情。
- 证据链页面和中文搜索入口。

非目标：

- 不依赖 Docker daemon。
- 不依赖 Redis / Celery。
- 不调用真实 embedding provider。
- 不调用真实 LLM provider。
- 不把 mock E2E 宣称成真实生产链路。

接口契约：

- Playwright 通过 `NEXT_PUBLIC_USE_MOCKS=true` 启动 Next.js dev server。
- E2E 使用中文用户可见文本和 role locator，不依赖英文内部实现。
- 失败产物默认保留 trace、screenshot、video 和 HTML report。

验收标准：

- `npm run test:e2e` 能在本地稳定运行。
- 至少覆盖首页、新建调研、任务、报告、证据链、retry 入口。
- E2E 不依赖真实外部模型或真实后端。
- 如果未接入 CI required check，需要在文档中说明原因和后续计划。

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

- 新增 Playwright 配置。
- 新增 E2E 测试：
  - 首页可打开。
  - 新建调研页可填写表单。
  - 任务列表可查看任务。
  - 失败任务详情可看到 `重试任务`。
  - 报告列表可进入报告详情。
  - 证据链页可看到评论语义检索。
- E2E 默认使用 mock dev server，避免依赖 Docker daemon。
- 失败产物保留 screenshot、trace、video 和 HTML report。

## 实施步骤

1. 先写 E2E 契约测试：
   - 确认 `package.json` 包含 `test:e2e`。
   - 确认 Playwright 配置指向 mock 环境。
   - 确认失败产物配置存在。
2. 安装并配置 Playwright。
3. 补齐 mock 模式下的 `createTask()`，避免新建调研仍请求真实后端。
4. 编写浏览器主链路 E2E：
   - 用中文 text / role locator。
   - 不依赖随机网络。
   - 不依赖真实 LLM provider。
5. 本地运行 E2E。
6. 根据稳定性决定后续是否纳入 CI required gate。

## 测试计划

计划执行：

```powershell
uv run pytest tests\test_day37_playwright_e2e_contract.py tests\test_frontend_localization_contract.py tests\test_frontend_retry_contract.py
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
npm run test:e2e
```

后端不参与 Day37 的浏览器 E2E。真实 API / Docker / Redis / Celery 模式必须在后续单独记录，不能和 Day37 mock E2E 混为同一个验收。

## 验收标准

- Playwright E2E 能在本地稳定运行。
- 至少覆盖首页、新建调研、任务、报告、证据链、retry 入口。
- E2E 使用中文可见文本和 role locator 做断言。
- E2E 不依赖真实外部模型或真实后端。
- 失败时能生成 screenshot、trace、video 和 HTML report。
- Playwright 产物目录不进入 Git，也不被 ESLint 当源码扫描。
- 如果没有接入 CI required check，必须在文档中说明原因和接入计划。

## 实际完成

Day37 按 SDD + TDD 完成 Playwright E2E 主链路接入。

实际改动：

- 新增 `frontend/playwright.config.ts`，使用 `127.0.0.1:3100` 的 mock dev server。
- 新增 `frontend/e2e/marketmind-main-flow.spec.ts`。
- 新增 `frontend/package.json` 脚本：`test:e2e`。
- 新增 `@playwright/test` dev dependency 并更新 `package-lock.json`。
- 更新 `frontend/.gitignore`，忽略 `playwright-report/` 和 `test-results/`。
- 更新 `frontend/eslint.config.mjs`，避免 lint 扫描 Playwright 产物。
- 更新 `frontend/src/lib/api.ts`，让 `NEXT_PUBLIC_USE_MOCKS=true` 时 `createTask()` 直接返回 mock task，不再依赖 FastAPI / Docker / Redis。
- 新增 `tests/test_day37_playwright_e2e_contract.py`，固定 E2E 配置、mock server、失败产物和中文 locator 契约。

E2E 覆盖路径：

1. 打开工作台首页，确认中文工作台、最近任务、最近报告可见。
2. 进入新建调研页，填写 `demo://e2e-negative-reviews`。
3. 在 mock 模式提交任务，跳转到任务详情。
4. 查看任务详情、事件时间线和 Agent 步骤。
5. 进入任务列表，打开失败任务 `tsk_6D44`。
6. 点击 `重试任务`，确认页面显示 `重试任务已提交`，并出现 `task.retry_submitted` 事件。
7. 进入报告列表，打开 `台灯差评分析` 报告详情。
8. 确认报告详情和 `证据引用` 可见。
9. 进入证据链页，确认 `评论语义检索` 和中文搜索框可见。

## TDD 过程

RED：

- `npm run test:e2e` 首次失败，原因是缺少 `test:e2e` 脚本。

GREEN 前暴露出的 UI 契约问题：

- 任务详情和报告详情页面的 H1 是业务标题，`任务详情` / `报告详情` 是 eyebrow。
- `Agent 步骤` 文本在描述和标题中重复，需要使用 heading locator。
- `重试任务已提交` 在提示和事件中重复，需要使用 exact locator。

这些问题不是业务功能错误，但说明 E2E 不能只做模糊文本匹配，需要跟页面可访问性结构对齐。

## 当前验证结果补充

```powershell
cd frontend
npm run test:e2e
# 1 passed

npm run lint
# passed

npm run build
# passed

npm audit --audit-level=high
# found 0 vulnerabilities

cd ..
uv run pytest tests\test_day37_playwright_e2e_contract.py
# 4 passed

uv run pytest tests\test_frontend_localization_contract.py tests\test_frontend_retry_contract.py tests\test_day33_retry_linkage_contract.py
# 17 passed
```

## 遗留问题

- 当前 E2E 是 mock browser E2E，不是 Docker Compose + FastAPI + Redis + Celery 的真实全链路 E2E。
- 当前只跑 Chromium desktop，尚未覆盖移动端 viewport。
- 当前没有接入 GitHub Actions required check；Day40 阶段验收时再决定是否纳入 CI required gate。
- 当前没有测试下载类交互，报告导出放到 Day38。

## 风险与回退

风险：

- E2E 因异步轮询不稳定。
- mock 模式环境变量在 Next.js 构建时被内联，导致真实 API 和 mock 行为混淆。
- Windows 本地浏览器依赖安装失败。
- CI 运行时间过长。

回退：

- 首版 E2E 只跑 mock 模式。
- 不把 E2E 立刻设为 required check，先观察稳定性。
- 对轮询页面使用明确等待条件，不使用固定 sleep。
- 真实 Compose E2E 作为后续增强，不阻塞 Day37。

## 文档同步清单

- `testing-strategy.md`：新增 Playwright E2E 边界、命令和产物。
- `development-log.md`：记录 Day37 本地验证结果。
- `interview-defense-dossier.md`：补充“如何证明前端真的可用”的回答。
- `phase-2-acceptance-and-risk.md`：记录 mock E2E 已完成，但真实 Compose E2E 未完成。
- `dev-workflow.md`：新增 `npm run test:e2e` 到前端验证门槛。
- `README.md`：更新 Playwright E2E 当前状态。

## 面试讲法

可以这样讲：

> Day37 我给项目补了 Playwright E2E。之前 API、状态机、RAG、报告都有测试，但浏览器端只能靠手动打开。E2E 覆盖中文首页、新建调研、任务详情、报告详情、证据链和失败重试入口，能证明这个系统不只是后端能跑，用户路径也能回归。

如果被问“为什么 E2E 先用 mock 模式”，回答：

> 因为 E2E 首要目标是稳定验证前端路径，不应该同时依赖 Docker daemon、Redis、Celery 和模型 provider。真实 API E2E 可以作为第二层验收，先把浏览器路径稳定下来更合理。

## 建议提交

```text
test: 增加 Playwright E2E 主链路
```
