# Day 19 - Next.js 前端真实 API 接入

## 当天目标

把 Next.js 控制台从“静态 mock 展示”推进到“可以向 FastAPI 发起真实任务”的阶段。Day 19 不追求一次性接完所有页面，而是优先打通最核心的前后端闭环：

1. 前端通过 `POST /api/tasks` 创建长任务。
2. 创建成功后跳转到 `/tasks/{task_id}`。
3. 任务详情页读取 `GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events`。
4. 对后端尚未实现的列表、Agent steps、报告详情等接口保留 mock fallback，避免前端因为未完成接口整体不可用。

这一日的关键判断是：前端接入必须诚实反映后端能力边界。稳定接口走真实 API，未实现接口保留降级路径，不在 UI 层伪造“全链路已完成”。

## 前置依赖

- `day-18.md` 已完成评论风险/机会评分，报告数据结构继续稳定。
- `../supporting/api-contract.md` 已定义统一 envelope、任务创建、任务状态、任务事件和报告证据链接口。
- `../supporting/ui-console-spec.md` 已定义控制台页面职责。
- `../supporting/stitch-frontend-handoff.md` 已确定 Stitch 只作为视觉参考，正式前端使用 Next.js。
- 后端当前稳定接口包括：
  - `POST /api/tasks`
  - `GET /api/tasks/{task_id}`
  - `GET /api/tasks/{task_id}/events`
  - `GET /api/reports/{report_id}/evidence`
- 后端当前尚未实现或不稳定的接口包括：
  - `GET /api/tasks`
  - `GET /api/tasks/{task_id}/steps`
  - `GET /api/reports`
  - `GET /api/reports/{report_id}`
  - `GET /api/evidence`

## 当天交付物

- 新增前端 API 接入契约测试：`tests/test_frontend_api_integration_contract.py`。
- 扩展 `frontend/src/lib/types.ts`，补齐任务创建、任务接受、后端状态映射需要的类型。
- 重构 `frontend/src/lib/api.ts`：
  - 统一读取 `NEXT_PUBLIC_API_BASE_URL`。
  - 使用 `NEXT_PUBLIC_USE_MOCKS=false` 切换真实 API 模式。
  - 封装 `ApiEnvelope<T>`。
  - 封装 `ApiClientError`，保留 `code`、`status`、`traceId` 和 `details`。
  - 新增 `createTask()` 调用真实 `POST /api/tasks`。
  - 任务状态和事件读取真实 API。
  - 未实现接口通过 `safeRequest()` 保留 fallback。
- 新增 `frontend/src/components/new-research-form.tsx`：
  - 客户端表单。
  - 提交 `target`、`mode`、`priority`、`source_type` 和 `options`。
  - 成功后展示 `task_id` 并跳转任务详情页。
  - 对 `ApiClientError` 展示明确错误码和错误信息。
- 更新 `frontend/src/app/research/new/page.tsx`，用真实表单替换静态 mock 表单。
- 更新 `frontend/src/components/app-shell.tsx`，显示当前 API 模式和 API base URL。
- 更新 `frontend/.env.example`，默认示例改为真实 API 模式。

## 实施步骤

### 1. 检查 Day 18 是否有遗漏

复查 Day 18 的代码和文档状态：

- Day 18 已有评分模块、schema、Markdown 展示和测试。
- `development-log.md` 已记录 Day 18。
- `interview-defense-dossier.md` 已记录 Day 18 的选择思考和面试问答。
- 上一轮验证包含 `uv run pytest`、`ruff`、`alembic heads` 和前端 build。

结论：Day 18 没有发现阻塞 Day 19 的遗漏。

### 2. 用契约测试锁定前端真实接入边界

新增 `tests/test_frontend_api_integration_contract.py`，不直接跑浏览器，而是用源码契约保证几个核心事实：

- API client 必须暴露 `createTask()`。
- API client 必须理解统一 envelope 和 `envelope.error`。
- 新建任务页面必须使用客户端组件提交，而不是静态表单。
- 成功后必须跳转 `/tasks/{task_id}`。
- 任务详情页继续调用 `getTask()`、`getTaskEvents()` 和 `getTaskSteps()`。
- Agent steps 在真实接口未实现时必须安全 fallback。
- Shell 和 `.env.example` 必须能暴露 API 模式。

这种测试不是替代 E2E，而是 Day 19 的低成本防回归网。Day 25 再补 Playwright 级别的完整用户流。

### 3. 封装真实 API client

`frontend/src/lib/api.ts` 的职责从“返回 mock data”升级为“真实 API 优先，mock 兜底”：

- `request<T>()` 统一发起 HTTP 请求。
- 成功路径要求 `envelope.success=true` 且 `envelope.data` 非空。
- 失败路径统一抛出 `ApiClientError`。
- `safeRequest<T>()` 只用于后端未实现接口的降级，不用于掩盖核心接口错误。
- `createTask()` 不走 fallback，因为任务创建是 Day 19 的核心交付。
- `getTask()` 和 `getTaskEvents()` 不走 fallback，因为任务详情应该真实反映后端状态。
- `getTaskSteps()` 暂时 `try/catch return []`，因为后端 steps API 还未实现。
- `listTasks()`、`listReports()`、`getReport()` 和 `listEvidence()` 暂时 fallback 到 mock data。

### 4. 接入新建任务页面

`NewResearchForm` 只负责提交任务，不负责业务分析：

- 表单输入：目标、数据源、分析模式。
- 选项输入：RAG、截图保存、Markdown 输出、失败自动重试标记。
- 提交 payload 与后端 `TaskCreateRequest` 对齐。
- 成功后跳转任务详情页。
- 失败时展示后端错误码，便于调试 `QUEUE_UNAVAILABLE`、`VALIDATION_FAILED` 等问题。

前端不拼 prompt、不跑 crawler、不做 RAG、不访问数据库。

### 5. 暴露 API 模式

AppShell 显示当前模式：

- `NEXT_PUBLIC_USE_MOCKS=false`：显示 `Real API` 和 API base URL。
- 其他情况：显示 `Mock` 和 mock client 状态。

这样调试时可以直接从页面判断当前是否连到真实后端，避免“以为在调真实接口，其实还在看 mock”的误判。

## 验收标准

- `uv run pytest tests\test_frontend_api_integration_contract.py` 通过。
- `cd frontend; npm run build` 通过。
- 新建任务页面渲染 `NewResearchForm`。
- `createTask()` 调用 `POST /api/tasks`。
- 成功后跳转 `/tasks/{task_id}`。
- API 错误通过 `ApiClientError` 显示错误码。
- `frontend/.env.example` 默认指向 `http://localhost:8000` 且 `NEXT_PUBLIC_USE_MOCKS=false`。
- 未实现接口保留显式 fallback，不影响当前可演示链路。

## 风险与回退

- 风险：后端没有启动时，真实模式下任务创建会失败。
  - 回退：开发调试可临时设置 `NEXT_PUBLIC_USE_MOCKS=true`。
- 风险：任务列表、报告详情、evidence 总览仍是 mock。
  - 回退：文档中明确标记，Day 20/Day 21 继续补接口和页面。
- 风险：前端过早引入复杂状态管理。
  - 回退：Day 19 暂不引入 React Query/SWR，先用已有 async functions 和页面组件保持边界简单。
- 风险：Agent steps API 尚未实现。
  - 回退：`getTaskSteps()` 在真实模式下返回空数组，Day 20 再做真实步骤展示。

## 关联文档

- 上一天：`day-18.md`
- 下一天：`day-20.md`
- 控制台：`../supporting/ui-console-spec.md`
- Stitch：`../supporting/stitch-frontend-handoff.md`
- API：`../supporting/api-contract.md`
- 开发日志：`../supporting/development-log.md`
- 面试手册：`../supporting/interview-defense-dossier.md`

## 建议提交

`feat: 实现 Day 19 前端真实 API 接入`
