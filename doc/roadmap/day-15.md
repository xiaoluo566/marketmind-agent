# Day 15 - 差评搜索工具

## 当天目标

为 Agent 提供 `search_reviews_tool`，让它能按语义寻找竞品缺陷，而不是靠模型凭空总结。

## 前置依赖

- `day-14.md` 向量检索可用
- 阅读 `../supporting/rag-memory.md`
- 阅读 `../supporting/agent-state-machine.md`

## 当天交付物

- `search_reviews_tool`
- 检索输入 schema
- 检索输出 schema
- 证据片段格式
- 召回为空时的降级逻辑

## 实施步骤

1. 定义输入：query、top_k、filter、task_id
2. 调用 pgvector 检索相关 chunk
3. 返回 chunk 内容、评分、来源、相似度
4. 对低相似度结果做过滤
5. 把工具接入 Agent 工具注册表

## 验收标准

- Agent 能通过“质量差”“物流慢”“退货”等词召回评论
- 检索结果可用于报告引用
- 召回为空时不会编造结论

## 风险与回退

- 召回结果质量差时先调整切片和 query，不急着换向量库
- top_k 不宜过大，避免又把上下文撑爆

## 关联文档

- 上一天：`day-14.md`
- 下一天：`day-16.md`
- 数据模型：`../supporting/data-model.md`
- 报告演示：`../supporting/demo-script.md`

## 建议提交

`feat: build review semantic search tool`

