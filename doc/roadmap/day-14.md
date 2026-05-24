# Day 14 - 向量检索基础

## 当天目标

把评论数据从普通文本变成可语义检索的知识库，为后续差评分析工具做准备。

## 前置依赖

- `day-13.md` 短期记忆已设计
- `day-09.md` 评论数据已入库
- 阅读 `../supporting/rag-memory.md`

## 当天交付物

- pgvector 扩展启用方案
- 评论切片流程
- embedding 生成流程
- 向量入库
- 相似度检索原型

## 实施步骤

1. 启用 pgvector
2. 定义 `review_chunks`
3. 编写评论清洗和切片函数
4. 调用 embedding 模型生成向量
5. 写入数据库并实现 top_k 检索

## 验收标准

- 一批评论能被切片和向量化
- 检索 query 能返回相关评论片段
- 返回结果包含相似度、review_id、source_url

## 风险与回退

- 如果 embedding 服务不可用，先用 fake embedding 跑通流程
- 不要把评论原文来源丢失

## 关联文档

- 上一天：`day-13.md`
- 下一天：`day-15.md`
- RAG：`../supporting/rag-memory.md`
- LLMOps：`../supporting/llmops-metrics.md`

## 建议提交

`feat: add pgvector retrieval`

