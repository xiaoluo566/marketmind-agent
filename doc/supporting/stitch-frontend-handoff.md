# Stitch 前端交接规范

## 决策

前端正式实现使用 Next.js。Stitch 导出作为视觉参考和页面结构参考。后端、API、数据库、任务系统、Agent 状态机、爬虫、RAG、报告生成、部署和测试由本仓库继续实现。

这个决策会替代早期文档里“第一版优先 Streamlit”的默认方案。后续优先走 Next.js 控制台 + FastAPI 后端接口集成的路线，Stitch 只保留为设计来源。

## 为什么这样分工

- Stitch 更适合快速生成视觉参考和页面结构
- Next.js 更适合作为可维护的正式前端工程
- 本项目的简历含金量主要在后端工程、异步任务、Agent 状态持久化和 RAG
- 前端不应占用过多时间，但必须能演示完整流程
- 前后端通过 API 契约解耦，避免 UI 生成工具影响后端架构

## Stitch 需要生成的页面

第一版只需要控制台，不做营销首页。

### 1. 任务提交页

必须包含：

- 商品链接输入框
- 可选数据上传入口
- 分析模式选择
- 提交按钮
- 提交后展示 `task_id`

### 2. 任务详情页

必须包含：

- 任务状态
- 当前阶段
- 进度条或步骤条
- 事件时间线
- Agent 工具调用摘要
- 失败错误码和提示

### 3. 报告详情页

必须包含：

- 报告摘要
- 竞品概况
- 差评痛点分析
- 风险评分
- 机会点
- 证据引用列表

### 4. 历史任务页

必须包含：

- 任务列表
- 状态筛选
- 时间筛选
- 报告入口
- 失败任务重试入口的预留位置

### 5. 设置页

第一版可以很简单，只预留：

- API base URL
- 模型提供方显示
- 当前环境显示

## 前端不要负责的内容

- 不做爬虫逻辑
- 不做 Agent 决策
- 不做评论向量检索
- 不拼接模型 prompt
- 不直接访问数据库
- 不保存 API key

## 前端需要遵守的 API 契约

前端只调用 FastAPI 暴露的接口：

- `POST /api/tasks`
- `GET /api/tasks/{task_id}`
- `GET /api/tasks/{task_id}/events`
- `GET /api/tasks/{task_id}/steps`
- `GET /api/reports/{report_id}`
- `POST /api/tasks/{task_id}/retry`

详细字段以 `api-contract.md` 和 `data-contract-examples.md` 为准。

## Day 19 接入状态

Day 19 已经在 `frontend/` 中完成第一批真实 API 接入：

- 任务提交页已经使用正式 Next.js 客户端组件，不再是静态表单。
- `POST /api/tasks`、`GET /api/tasks/{task_id}` 和 `GET /api/tasks/{task_id}/events` 已接入真实 FastAPI。
- `frontend/.env.example` 默认使用 `NEXT_PUBLIC_USE_MOCKS=false`。
- AppShell 会显示当前是 `Real API` 还是 `Mock`。

Stitch 后续如果重新生成页面，需要注意：

- 不要覆盖 `frontend/src/lib/api.ts` 中的真实 API client。
- 不要把 `NewResearchForm` 改回静态按钮。
- 不要在页面里硬编码 `localhost`，应继续使用 `NEXT_PUBLIC_API_BASE_URL`。
- 不要在前端补写 crawler、Agent、RAG 或 prompt 逻辑。
- 对后端尚未实现的接口，可以保留 mock 展示，但必须在代码或文档中标注为 fallback。

## Stitch 生成代码交接要求

你从 Stitch 导出后，最好提供以下内容：

- 前端项目目录
- 使用的框架，例如 Next.js、React、Vite
- 样式方案，例如 Tailwind、CSS Modules
- 页面截图或预览链接
- 组件文件结构
- 是否带 mock data
- 是否已经写死 API URL

## Stitch 提示词

具体生成提示词见 `stitch-generation-prompt.md`。后续如果页面结构或接口字段变化，优先更新那份提示词，再重新生成或局部改造前端。

## 我接手前端集成时需要检查

- 是否有硬编码假数据
- 是否有硬编码 localhost 地址
- 是否有重复状态管理
- 是否存在页面无法接真实 API 的结构
- 是否有明显移动端或桌面布局问题
- 是否适合接入任务轮询或 SSE

## 第一阶段集成策略

1. 保留 Stitch 导出作为设计参考
2. 在 `frontend/` 中用 Next.js 重建可维护组件和路由
3. 后端 API 完成后，把 mock data 替换成 API client
4. 先用轮询实现任务进度
5. 后续再升级到 SSE 或 WebSocket
6. 前端只展示 Agent step 摘要，不展示敏感 prompt 或完整模型输入

## 与其他文档关系

- 页面规格见 `ui-console-spec.md`
- API 字段见 `api-contract.md`
- 数据样例见 `data-contract-examples.md`
- 第 19 到 21 天会进入前端集成阶段
