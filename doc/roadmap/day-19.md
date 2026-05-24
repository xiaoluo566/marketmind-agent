# Day 19 - 前端控制台骨架

## 当天目标

把 Stitch 生成的前端控制台接入真实后端 API。第一版重点不是重新设计 UI，而是把任务提交、状态查询和报告入口接到真实接口。

## 前置依赖

- `day-18.md` 报告数据结构已稳定
- 阅读 `../supporting/ui-console-spec.md`
- 阅读 `../supporting/stitch-frontend-handoff.md`
- API 接口可访问
- Stitch 已导出前端项目或页面代码

## 当天交付物

- Stitch 前端项目接入仓库
- 任务提交表单
- 任务列表页
- 报告详情入口
- API client 基础封装

## 实施步骤

1. 检查 Stitch 导出的项目结构
2. 清理明显的 mock-only 逻辑
3. 封装 API client
4. 接入 `POST /api/tasks`
5. 展示提交后的 task_id
6. 展示任务列表和状态
7. 点击任务进入详情页

## 验收标准

- 不用命令行也能发起任务
- 前端能显示任务状态
- API 错误能展示给用户
- Stitch 生成代码中没有不可控的硬编码 API 地址

## 风险与回退

- 不要在前端写业务分析逻辑
- 如果 Stitch 生成的状态管理复杂，先保留页面结构，逐步替换数据层
- 第一版先用轮询而不是 WebSocket

## 关联文档

- 上一天：`day-18.md`
- 下一天：`day-20.md`
- 控制台：`../supporting/ui-console-spec.md`
- Stitch：`../supporting/stitch-frontend-handoff.md`
- API：`../supporting/api-contract.md`

## 建议提交

`feat: integrate stitch control panel shell`
