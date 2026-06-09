# Day 31 - 中文界面与术语统一

## 当天目标

Day 31 是第二阶段的第一个开发日。目标是先文档后开发，把 Next.js 控制台从英文模板式界面推进到中文运营工作台。

当天不追求重做设计，也不引入复杂 i18n 框架。重点是统一核心可见文案，让页面语言和项目定位一致：

- 左侧导航。
- 顶部环境状态。
- Dashboard 首页。
- 新建调研页和 `NewResearchForm`。
- 任务列表、任务详情和 Agent steps。
- 报告列表、报告详情和证据链。
- evidence 总览页。
- settings 页。
- status badge 和常见按钮。

## 前置依赖

- `phase-2-master-plan.md`
- `../supporting/frontend-localization-contract.md`
- `../supporting/phase-2-practicality-plan.md`
- `../supporting/ui-console-spec.md`
- `../supporting/stitch-frontend-handoff.md`

## 当天交付物

- 新增 `tests/test_frontend_localization_contract.py`。
- 把核心前端页面和组件的可见英文文案替换为中文。
- 保留 API 字段名、路径、状态枚举、模型名、trace id、task id、report id 等技术标识。
- 更新 `frontend-localization-contract.md` 的完成记录。
- 更新 `development-log.md` 和 `interview-defense-dossier.md`。

## 实施步骤

1. 先写前端中文化契约测试。
2. 扫描 `frontend/src` 中的英文展示文案。
3. 按 `frontend-localization-contract.md` 的中文术语表替换可见文本。
4. 优先替换 AppShell 导航和顶部状态，因为它会出现在所有页面。
5. 替换 Dashboard 页面，包括标题、统计卡片、最近任务、系统链路、最近报告。
6. 替换 `NewResearchForm` 的 label、placeholder、错误提示和提交按钮。
7. 替换任务、报告、证据链、设置页中的面向用户文案。
8. 保留代码变量名，不为了中文化重命名 API 字段。
9. 跑前端 lint/build 和文档测试。

## 文案替换原则

- `Dashboard` -> `工作台`
- `New Research` -> `新建调研`
- `Tasks` -> `任务`
- `Reports` -> `报告`
- `Evidence` -> `证据链`
- `Settings` -> `设置`
- `Recent tasks` -> `最近任务`
- `System chain` -> `系统链路`
- `Recent reports` -> `最近报告`
- `Success rate` -> `成功率`
- `Validation errors` -> `校验错误`
- `Agent research operations` -> `Agent 调研工作台`
- `Evidence cockpit` -> `证据链控制台`

详细术语见 `../supporting/frontend-localization-contract.md`。

## 验收标准

- `tests/test_frontend_localization_contract.py` 通过。
- `npm run lint` 通过。
- `npm run build` 通过。
- 页面主要标题、导航、按钮、表单 label 和状态提示为中文。
- API 字段名、枚举值和技术标识不被误翻译。
- 不引入复杂 i18n 框架。

## 实际完成记录

Day31 已完成第二阶段中文界面基线，不只是改首页文案，而是把核心控制台链路全部纳入中文术语：

- `AppShell`：导航、环境状态、API 模式、刷新按钮统一为中文。
- Dashboard：首页标题、统计卡片、最近任务、系统链路、最近报告统一为中文。
- `NewResearchForm`：数据来源、分析模式、表单 label、placeholder、错误提示、提交成功提示统一为中文。
- Tasks：任务列表、任务详情、轮询状态、刷新按钮、打开报告入口统一为中文。
- Reports：报告列表、报告详情、风险评分、证据引用统一为中文。
- Evidence：评论语义检索、评分筛选、已选证据说明统一为中文。
- Settings：本地联调设置和功能开关使用中文 label，同时保留 `enable_rag` 等技术 key。
- `StatusBadge`：任务状态、Agent step 状态、系统状态、风险等级统一映射中文 label，不再依赖英文 fallback。
- `formatDateTime()`：从英文月份格式切换到 `zh-CN` 日期格式，避免中文页面出现英文月份。
- `layout.tsx`：HTML `lang` 从 `en` 切到 `zh-CN`，metadata description 改成中文语境。
- `mock-data.ts`：演示数据中的用户可见服务说明、任务标题、事件消息、证据内容和报告摘要同步中文化。

新增和扩展的测试：

- `tests/test_frontend_localization_contract.py`：覆盖 AppShell、Dashboard、NewResearchForm、任务/报告/证据/设置页面、进度组件、状态 badge、mock 文案和中文日期格式。
- `tests/test_phase2_planning_docs.py`：继续约束第二阶段文档入口和后续优先级。

本日验证结果：

```powershell
uv run pytest tests\test_frontend_localization_contract.py tests\test_phase2_planning_docs.py
# 12 passed

uv run pytest
# 180 passed

uv run pytest --cov=backend --cov-report=term-missing
# 180 passed, backend coverage 90.77%

uv run ruff check backend tests migrations
# All checks passed

uv run alembic heads
# 0002_task_queue_id (head)

docker compose config
# passed

cd frontend
npm run lint
# passed

npm run build
# passed

npm audit --audit-level=high
# found 0 vulnerabilities
```

浏览器验收：

- `NEXT_PUBLIC_USE_MOCKS=true npm run dev -- --hostname 127.0.0.1 --port 3002`。
- HTTP 检查 `/`、`/research/new`、`/tasks`、`/reports`、`/evidence`、`/settings` 全部返回 200。
- `agent-browser-cli` 扫描确认首页显示 `API 模拟客户端已启用`、`模拟模式`、`Agent 调研工作台`。
- `agent-browser-cli` 扫描确认任务页显示 `调研任务历史`，报告页显示 `已生成调研报告`，证据页显示 `评论语义检索`，设置页显示 `本地联调设置`。

说明：本日只验证了 `docker compose config`，没有声明真实 `docker compose build/up` 已完成。真实容器联调仍按第二阶段计划等待 Docker daemon 可用后补验。

注意：`NEXT_PUBLIC_USE_MOCKS` 属于 Next.js public env，生产构建中会被内联。要演示 mock 模式，需要在 `npm run dev` 启动时设置该变量，或在生产构建前设置该变量后重新 `npm run build`。默认 `.env.example` 仍保持真实 API 策略。

## 风险与回退

风险：

- 直接替换字符串可能误改 API 字段或类型值。
- 中文文本比英文长，可能导致按钮或卡片挤压。
- 部分 mock 数据本身是英文商品名或评论摘要，第一天不强行翻译业务样例。

回退：

- 如果构建失败，优先回退具体页面文案改动，不回退整阶段文档。
- 如果布局被中文撑坏，先缩短文案或调整容器，不改回英文。
- 如果发现需要完整 i18n，再写新设计文档，不在 Day31 临时引入框架。

## 与后续开发关系

Day31 完成后，Day32 的前端 retry 按钮必须使用中文文案，例如 `重试任务`、`正在重新投递`、`恢复事件`。真实 provider、LLMOps 和 E2E 也都要沿用本日术语。

## 建议提交

```text
feat: 完成第二阶段中文界面基线
```
