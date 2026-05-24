# Day 19 - 前端控制台骨架

## 当天目标

做一个能提交任务、查看状态和打开报告的最小控制台。第一版优先使用 Streamlit，降低前端开发成本。

## 前置依赖

- `day-18.md` 报告数据结构已稳定
- 阅读 `../supporting/ui-console-spec.md`
- API 接口可访问

## 当天交付物

- 控制台入口
- 任务提交表单
- 任务列表页
- 报告详情入口

## 实施步骤

1. 创建前端 app 目录
2. 接入 `POST /api/tasks`
3. 展示提交后的 task_id
4. 展示任务列表和状态
5. 点击任务进入详情页

## 验收标准

- 不用命令行也能发起任务
- 前端能显示任务状态
- API 错误能展示给用户

## 风险与回退

- 不要在前端写业务分析逻辑
- 如果 Streamlit 状态管理复杂，先用轮询而不是 WebSocket

## 关联文档

- 上一天：`day-18.md`
- 下一天：`day-20.md`
- 控制台：`../supporting/ui-console-spec.md`
- API：`../supporting/api-contract.md`

## 建议提交

`feat: add control panel shell`

