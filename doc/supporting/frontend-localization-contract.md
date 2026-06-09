# 前端中文化契约

## 文档定位

这份文档定义第二阶段前端中文界面的术语、范围、非目标和测试契约。它不是翻译表的临时备忘录，而是后续页面、测试、演示和面试表达都要遵守的语言边界。

关联文档：

- `../roadmap/phase-2-master-plan.md`
- `../roadmap/day-31.md`
- `ui-console-spec.md`
- `stitch-frontend-handoff.md`
- `phase-2-practicality-plan.md`

## 中文术语表

| 英文/技术词 | 中文界面文案 | 说明 |
| --- | --- | --- |
| Dashboard | 工作台 | 首页总览，不使用“仪表盘”以避免泛化 |
| New Research | 新建调研 | 用户提交新任务的入口 |
| Tasks | 任务 | 长任务列表 |
| Reports | 报告 | 结构化运营报告 |
| Evidence | 证据链 | 评论 chunk、artifact、Agent step 的来源回查 |
| Settings | 设置 | 环境、模型、数据源配置页 |
| Agent steps | Agent 步骤 | Thought / Action / Observation 的展示层 |
| Recent tasks | 最近任务 | 首页任务摘要 |
| Recent reports | 最近报告 | 首页报告摘要 |
| System chain | 系统链路 | API、Crawler、Agent、RAG、Report 等模块 |
| Success rate | 成功率 | 不写成“通过率”，避免和测试通过率混淆 |
| Validation errors | 校验错误 | Pydantic / Guardrails 错误 |
| Retry | 重试 | failed 任务再次投递 |
| Recovery | 恢复 | retry 后的恢复状态和事件 |
| Evidence refs | 证据引用 | 报告中引用的证据 ID |
| Trace ID | Trace ID | 技术标识保留英文 |
| Task ID | Task ID | 技术标识保留英文 |
| Report ID | Report ID | 技术标识保留英文 |

## 页面范围

Day31 中文化覆盖：

- `frontend/src/components/app-shell.tsx`
- `frontend/src/app/page.tsx`
- `frontend/src/app/research/new/page.tsx`
- `frontend/src/components/new-research-form.tsx`
- `frontend/src/app/tasks/page.tsx`
- `frontend/src/app/tasks/[taskId]/page.tsx`
- `frontend/src/components/task-progress-panel.tsx`
- `frontend/src/components/agent-steps-table.tsx`
- `frontend/src/app/reports/page.tsx`
- `frontend/src/app/reports/[reportId]/page.tsx`
- `frontend/src/components/report-viewer.tsx`
- `frontend/src/app/evidence/page.tsx`
- `frontend/src/components/evidence-list.tsx`
- `frontend/src/app/settings/page.tsx`
- `frontend/src/components/status-badge.tsx`

## 非目标

Day31 暂不引入复杂 i18n 框架。

原因：

- 当前项目只有中文目标用户和中文面试展示，不需要多语言切换。
- 引入 i18n 会增加 routing、dictionary、server/client boundary 和测试复杂度。
- 当前更重要的是稳定术语，而不是支持多语言市场。

Day31 不做：

- 不翻译 API 字段名。
- 不翻译 TypeScript 类型、枚举值、数据库字段。
- 不翻译 model name、provider name、trace id、task id、report id。
- 不翻译 fixture 商品名，除非它是明确的 UI label。
- 不重做 UI 视觉设计。

明确要求：不要翻译 API 字段名。比如 `task_id`、`report_id`、`evidence_refs`、`created_at` 必须保持原样。

## 测试契约

新增 `tests/test_frontend_localization_contract.py`，至少覆盖：

- AppShell 导航不再出现 Dashboard、New Research、Tasks、Reports、Evidence、Settings。
- AppShell 导航出现 工作台、新建调研、任务、报告、证据链、设置。
- Dashboard 页面出现 Agent 调研工作台、最近任务、系统链路、最近报告。
- NewResearchForm 出现中文 label、placeholder 和按钮。
- status badge 能显示中文状态。
- API 字段名和枚举值不被误翻译。
- 任务、报告、证据链、设置和进度组件不再保留核心英文标题。
- 设置页必须显示中文开关名，同时保留 `enable_rag` 等技术 key。
- 日期格式必须使用 `zh-CN`，避免中文页面出现英文月份。
- 根布局必须使用 `lang="zh-CN"` 和中文 metadata description。

## Day31 完成记录

Day31 已把本契约落到代码和测试：

- `frontend/src/components/app-shell.tsx` 已使用中文导航和中文环境状态。
- `frontend/src/app/page.tsx` 已使用中文工作台标题、指标和列表标题。
- `frontend/src/components/new-research-form.tsx` 已使用中文表单文案，并保留 `source_type`、`use_rag`、`priority`、`options` 等 API 字段。
- `frontend/src/app/tasks/page.tsx`、`frontend/src/app/tasks/[taskId]/page.tsx`、`frontend/src/components/task-progress-panel.tsx`、`frontend/src/components/task-timeline.tsx` 已完成任务链路中文化。
- `frontend/src/app/reports/page.tsx`、`frontend/src/app/reports/[reportId]/page.tsx`、`frontend/src/components/report-viewer.tsx` 已完成报告链路中文化。
- `frontend/src/app/evidence/page.tsx`、`frontend/src/components/evidence-list.tsx` 已完成证据链中文化。
- `frontend/src/app/settings/page.tsx` 已完成本地联调设置中文化，功能开关采用中文 label + 技术 key 的双层展示。
- `frontend/src/lib/utils.ts` 已把时间格式切换到 `zh-CN`。
- `frontend/src/app/layout.tsx` 已把 HTML 语言和 metadata description 调整为中文语境。

当前验证：

```powershell
uv run pytest tests\test_frontend_localization_contract.py tests\test_phase2_planning_docs.py
# 12 passed

cd frontend
npm run lint
npm run build
npm audit --audit-level=high
# lint/build passed, audit found 0 vulnerabilities
```

浏览器验收使用 `NEXT_PUBLIC_USE_MOCKS=true` 的 dev server。注意 `NEXT_PUBLIC_*` 在生产构建中会被内联，不能只在 `next start` 时注入变量来判断客户端顶部模式 badge。

## 后续扩展

如果未来需要英文版或多语言：

1. 先新增 i18n 设计文档。
2. 再决定使用 dictionary、next-intl 或自研轻量映射。
3. 再把当前中文硬编码迁移到字典。
4. 迁移前必须保留现有中文页面测试，避免多语言引入后中文体验退化。
