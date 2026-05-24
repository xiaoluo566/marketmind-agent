# Day 21 - 历史记录与报告列表

## 当天目标

让系统具备积累价值。用户不仅能跑一次任务，还能回看历史任务、历史报告和失败记录。

## 前置依赖

- `day-20.md` 任务详情可展示
- 阅读 `../supporting/ui-console-spec.md`
- 阅读 `../supporting/data-model.md`

## 当天交付物

- 历史任务列表
- 报告列表
- 状态筛选
- 时间筛选
- 报告详情跳转

## 实施步骤

1. 增加任务列表 API 或复用已有查询接口
2. 前端展示最近任务
3. 支持按状态筛选 completed、failed、running
4. 报告列表显示标题、生成时间、任务状态
5. 点击报告进入报告详情

## 验收标准

- 历史任务能被查到
- 老报告能被打开
- 失败任务不会从列表里消失

## 风险与回退

- 不要为了历史列表引入复杂权限
- 第一版分页可以简单实现，但要保留扩展口

## 关联文档

- 上一天：`day-20.md`
- 下一天：`day-22.md`
- 控制台：`../supporting/ui-console-spec.md`
- API：`../supporting/api-contract.md`

## 建议提交

`feat: add history and archives`

