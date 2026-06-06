# 测试策略

## 测试层次

1. 单元测试：工具函数、校验器、格式化器
2. 集成测试：API、数据库、任务队列
3. 端到端测试：任务提交到报告生成的完整链路

## 测试映射

| 模块 | 测试类型 | 重点 |
| --- | --- | --- |
| API | 集成测试 | 输入校验、错误码、task_id 返回 |
| Celery | 集成测试 | 任务投递、状态更新、重试 |
| Crawler | 单元 + 集成 | DOM 抽取、失败分类、证据保存 |
| Agent | 单元 + 集成 | 状态转移、工具调用、断点恢复 |
| RAG | 单元 + 集成 | 切片、embedding、召回 |
| Report | 单元 | schema、引用、摘要结构 |
| Frontend | E2E | 提交任务、查看进度、查看报告 |

## 必测内容

- Pydantic schema 校验
- Agent 状态流转
- Celery 任务投递与重试
- 评论切片与向量检索
- 报告生成

## 测试原则

- 失败要可复现
- 关键路径要自动化
- 修 bug 必须补回归测试

## 验收门槛

- 核心模块有测试
- 关键路径能跑通
- 回退版本能快速验证

## 测试数据策略

- 保留少量固定 HTML 样例
- 保留评论 CSV / JSON 样例
- 保留模型输出失败样例
- 保留 Agent step 恢复样例

## Day 14 RAG 测试边界

Day 14 新增 `tests/test_review_rag_indexing.py`，当前覆盖：

- 评论 HTML / script 清洗。
- 按句子边界切片。
- fake embedding 稳定性和维度。
- `review_chunks` 幂等入库。
- top_k 相似评论检索返回 `review_id`、`source_url`、`rating` 和 `similarity`。

当前没有覆盖真实 embedding API 和 PostgreSQL pgvector 原生排序。后续接真实 provider 和 Docker Compose PostgreSQL 后，需要补：

- provider 超时和重试。
- embedding 维度不匹配失败。
- pgvector `<=>` 排序结果。
- 相似度阈值过低时的“证据不足”行为。

## Day 15 工具测试边界

Day 15 新增 `tests/test_search_reviews_tool.py`，当前覆盖：

- 传入 RAG store 和 embedding provider 后，registry 能注册 `search_reviews_tool`。
- query 命中评论时，工具返回 evidence chunk 和 `chunk:{chunk_id}` 格式的 evidence ref。
- `rating_lte` 过滤可以保留低分差评。
- 高 `min_similarity` 导致召回为空时，工具返回空 `results`、空 `evidence_refs` 和 `NO_REVIEW_CHUNKS_ABOVE_THRESHOLD`。

后续 Day 16 - Day 17 报告测试需要验证：

- 报告只能引用 `evidence_refs` 中出现过的 chunk。
- `no_results_reason` 存在时，报告必须标注证据不足。
- 不能把 query 本身写成事实。

## Day 16 报告生成测试边界

Day 16 新增 `tests/test_report_generation.py`，当前覆盖：

- `StructuredReport` 拒绝章节引用未知 evidence ref。
- 没有 evidence snippets 时，生成 `insufficient_evidence` 报告。
- 无证据报告不编造 evidence refs，并在 claim 中明确“证据不足”。
- 有 evidence snippets 时，报告章节能绑定已知 evidence refs。
- `StructuredReport.to_markdown()` 能输出标题、摘要、章节、风险等级和证据引用。
- `SQLAlchemyReportStore` 能把报告 JSON、Markdown、evidence refs 和 schema version 写入 `reports` 表。

Day 16 当前不覆盖：

- 真实 LLM report prompt 输出。
- 多版本报告覆盖策略。
- 报告 API 路由。
- 前端报告详情页。
- PDF / Markdown 文件导出。

这些内容分别放到 Day 17 - Day 21 和第四周处理。Day 16 的测试重点是防止“无证据也生成结论”和“章节引用不存在证据”这两个高风险问题。

## 回归要求

任何 bug 修复都要留下一个能复现旧问题的测试。没有测试的修复，后续很容易被重构再次破坏。

## 与其他文档关系

- 数据样例见 `data-contract-examples.md`
- 状态机见 `agent-state-machine.md`
- 发版门槛见 `release-checklist.md`
