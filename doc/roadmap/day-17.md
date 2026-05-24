# Day 17 - 证据链与引用

## 当天目标

让报告里的关键判断能追溯到原始评论、页面、截图或工具输出。没有证据的结论不能写成事实。

## 前置依赖

- `day-16.md` 报告结构已生成
- 阅读 `../supporting/rag-memory.md`
- 阅读 `../supporting/crawler-strategy.md`

## 当天交付物

- citation 格式
- evidence_id 设计
- 报告引用渲染
- 来源回查接口

## 实施步骤

1. 为 review chunk、artifact、agent step 生成可引用 ID
2. 报告结论绑定 evidence_id
3. 前端展示证据摘要和来源链接
4. 数据库保留引用关系
5. 对证据不足的结论明确标注不确定性

## 验收标准

- 报告中的关键段落能跳转到证据
- 证据能追到原始评论或页面
- 证据缺失时报告不强行下结论

## 风险与回退

- 引用格式不要只存在 Markdown 文本里
- 不要把证据 ID 和数据库主键混用到难以迁移

## 关联文档

- 上一天：`day-16.md`
- 下一天：`day-18.md`
- 数据模型：`../supporting/data-model.md`
- 演示：`../supporting/demo-script.md`

## 建议提交

`feat: attach evidence chain to reports`

