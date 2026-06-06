# 控制台规格

## 目标

控制台不是装饰，而是让你能提交任务、观察任务、查看报告、回放失败过程的操作面板。

## 第一版页面

正式前端使用 Next.js + TypeScript + Tailwind 实现。Stitch 输出作为视觉参考源，本仓库负责接口契约、后端实现和前端接入。页面视觉与组件结构可以参考 Stitch，但页面职责必须符合本文件。

- 任务提交页
- 任务详情页
- 实时进度页
- 报告页
- 历史记录页
- 调试和设置页

## 任务进度数据格式

前端实时进度页不直接解析日志，而是消费后端的结构化任务状态和事件流。

## Day 19 实际接入边界

Day 19 已把控制台的核心任务入口接到真实 FastAPI：

- `frontend/src/components/new-research-form.tsx` 调用 `POST /api/tasks` 创建任务。
- 创建成功后跳转到 `/tasks/{task_id}`。
- 任务详情页通过 `GET /api/tasks/{task_id}` 读取状态快照。
- 任务详情页通过 `GET /api/tasks/{task_id}/events` 读取事件时间线。
- AppShell 显示当前 API 模式，避免调试时误把 mock 当成真实接口。

Day 19 仍然保留 fallback 的页面或数据：

- 任务列表：后端 `GET /api/tasks` 尚未实现。
- Agent steps：后端 `GET /api/tasks/{task_id}/steps` 尚未实现，前端暂时返回空数组。
- 报告列表和报告详情：后端 `GET /api/reports`、`GET /api/reports/{report_id}` 尚未实现。
- evidence 总览：后端 `GET /api/evidence` 尚未实现。

这意味着 Day 20 的优先级不是继续堆静态页面，而是补任务进度刷新和 Agent step 的真实展示。

### 状态快照

`GET /api/tasks/{task_id}` 返回的数据建议用于任务详情页的顶部摘要：

- `task_id`
- `status`
- `trace_id`
- `target`
- `mode`
- `priority`
- `source_type`
- `queue_task_id`
- `error_code`
- `error_message`
- `created_at`
- `updated_at`

### 事件时间线

`GET /api/tasks/{task_id}/events` 返回的数据建议用于时间线组件：

- `event_id`
- `task_id`
- `status`
- `event_type`
- `message`
- `payload`
- `trace_id`
- `created_at`

展示规则：

- 按 `created_at` 排序。
- `error` 类型事件用单独颜色或图标。
- `payload` 只在详情展开时显示。
- 失败时优先展示 `message` 和 `error_code`，不要让用户翻日志。

## 页面职责

### 任务提交页

- 输入目标链接、主题或手工数据
- 选择分析模板
- 提交后立即返回 `task_id`

### 任务详情页

- 展示任务状态
- 展示事件时间线
- 展示 Agent 步骤
- 展示当前失败点和重试点

### 报告页

- 展示摘要、维度分析、风险点、证据链
- 支持导出 Markdown

## 组件约束

- 状态必须可刷新
- 失败信息必须显式显示
- 长文本必须可折叠
- 关键指标必须一眼可见

## 后端依赖

这个页面依赖 `api-contract.md`、`observability.md` 和 `agent-state-machine.md`。

## Stitch 交接

Stitch 相关前端生成和交接要求见 `stitch-frontend-handoff.md`。
