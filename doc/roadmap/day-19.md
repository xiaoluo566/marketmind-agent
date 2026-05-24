# Day 19 - 前端控制台骨架

## 当天目标

把 Next.js 前端控制台接入真实后端 API。Stitch 导出作为视觉参考，第一版重点是把任务提交、状态查询和报告入口接到真实接口。

## 前置依赖

- `day-18.md` 报告数据结构已稳定
- 阅读 `../supporting/ui-console-spec.md`
- 阅读 `../supporting/stitch-frontend-handoff.md`
- API 接口可访问
- Stitch 已导出设计参考或 Next.js 控制台骨架已存在

## 当天交付物

- Next.js 前端项目接入仓库
- 任务提交表单
- 任务列表页
- 报告详情入口
- API client 基础封装

## 实施步骤

1. 检查 Next.js 项目结构
2. 对照 Stitch 导出校准页面结构和视觉风格
3. 清理明显的 mock-only 逻辑
4. 封装 API client
5. 接入 `POST /api/tasks`
6. 展示提交后的 task_id
7. 展示任务列表和状态
8. 点击任务进入详情页

## 验收标准

- 不用命令行也能发起任务
- 前端能显示任务状态
- API 错误能展示给用户
- Next.js 代码中没有不可控的硬编码 API 地址

## 风险与回退

- 不要在前端写业务分析逻辑
- 如果状态管理变复杂，先保留页面结构，逐步替换数据层
- 第一版先用轮询而不是 WebSocket

## 关联文档

- 上一天：`day-18.md`
- 下一天：`day-20.md`
- 控制台：`../supporting/ui-console-spec.md`
- Stitch：`../supporting/stitch-frontend-handoff.md`
- API：`../supporting/api-contract.md`

## 建议提交

`feat: 接入 Next.js 控制台骨架`
