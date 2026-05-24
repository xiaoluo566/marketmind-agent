# Stitch 导出评审

## 当前导出目录

`stitch_marketmind_control_center/`

## 已有页面

- `dashboard_marketmind_agent`
- `new_research_marketmind_agent`
- `task_detail_marketmind_agent`
- `task_history_marketmind_agent`
- `reports_analysis_marketmind_agent`
- `evidence_retrieval_marketmind_agent`
- `settings_marketmind_agent`
- `marketmind_industrial/DESIGN.md`

## 初步判断

Stitch 输出已经覆盖本项目第一版需要的主要控制台页面，视觉方向也基本符合 `stitch-generation-prompt.md` 中的 industrial SaaS / developer operations 要求。

当前导出形态是多个独立 HTML 文件和截图，适合作为设计参考源，但还不是可维护的前端工程。正式前端已经确定使用 Next.js，应当把这些页面重构为统一的 `frontend/` 应用，并抽取公共组件。

## 需要保留的设计要点

- 左侧导航 + 顶部状态栏 + 主内容区
- 工业化浅色控制台风格
- Inter + JetBrains Mono 字体组合
- 状态颜色映射
- Agent step、任务状态、证据检索、报告详情这些核心页面结构

## 后续改造方向

1. 以 Stitch HTML 为视觉参考，不直接把所有 HTML 拼成生产前端
2. 抽取共享布局：`AppShell`、`Sidebar`、`TopStatusBar`
3. 抽取共享组件：`StatusBadge`、`TaskTimeline`、`AgentStepsTable`、`EvidenceList`、`ReportViewer`
4. 集中 mock data 到 `frontend/src/lib/mock-data.ts`
5. 集中 API 调用到 `frontend/src/lib/api.ts`

## 与其他文档关系

- Stitch 提示词见 `stitch-generation-prompt.md`
- 前端交接见 `stitch-frontend-handoff.md`
- 页面规格见 `ui-console-spec.md`
