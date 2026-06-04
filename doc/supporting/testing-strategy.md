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

## 回归要求

任何 bug 修复都要留下一个能复现旧问题的测试。没有测试的修复，后续很容易被重构再次破坏。

## 与其他文档关系

- 数据样例见 `data-contract-examples.md`
- 状态机见 `agent-state-machine.md`
- 发版门槛见 `release-checklist.md`
