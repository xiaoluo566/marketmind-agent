# Day 30 - 里程碑验收与发布候选

## 当天目标

确认第一阶段项目已经具备可展示、可复盘、可继续扩展的状态。今天要打版本、跑演示、总结数据和列下一阶段计划。

## 前置依赖

- `day-29.md` 文档和演示材料已整理
- 阅读 `../supporting/release-checklist.md`
- 阅读 `../supporting/milestones-and-acceptance.md`

## 当天交付物

- release candidate
- Git tag
- metrics summary
- bug summary
- next iteration list
- demo recording 或截图材料

## 实施步骤

1. 从空环境跑启动流程
2. 跑完整演示任务
3. 跑测试
4. 检查日志和失败记录
5. 汇总性能、成本、成功率
6. 创建版本 tag
7. 推送 GitHub

## 验收标准

- 主链路可演示
- 文档能指导复现
- 关键指标已记录
- 失败和不足已写明
- 下一阶段计划清楚

## 风险与回退

- 如果 release checklist 未通过，不要打正式版本
- 如果演示链路不稳定，保留 RC tag，不宣称 v1.0

## 关联文档

- 上一天：`day-29.md`
- 总计划：`30-day-master-plan.md`
- 发版：`../supporting/release-checklist.md`
- 后续：`../supporting/future-iterations.md`

## 建议提交

`release: candidate for first public demo`

