# 真实应用闭环说明

## 背景

当前项目不再优先继续堆 Agent 层能力，而是先证明系统能处理真实电商运营场景中的评论输入，并输出可追踪的证据链报告。

核心闭环：

```text
CSV/JSON 评论导入
-> 数据清洗、错误行报告、去重、入库
-> RAG 评论切片和质量评估
-> evidence-bound LLM 报告
-> 前端展示结论、引用证据、原始评论
```

## 已落地能力

### CSV/JSON 评论导入

接口：`POST /api/imports/reviews`

导入后系统会创建 `source_type=manual_upload`、`status=completed` 的 task，写入 product 和有效 review，并返回错误行明细、去重统计和 `task_id`。

### 低风险真实站点适配器

当前不适配淘宝、京东等强反爬平台。低风险入口选择 JSON-LD `Product.review`：

- 适用于公开独立站、Shopify 风格商品页、本地 HTML fixture。
- 只读取页面公开 HTML 中的 `application/ld+json`。
- 不绕过登录、验证码、付费墙或安全策略。

### RAG 质量评估

已有 `RAGEvaluationCase` 和 `evaluate_rag_quality()`，用 query 和 expected review ids 验证召回质量。

### evidence-bound LLM 报告

已有 `LLMStructuredReportGenerator`，prompt 中显式提供 evidence refs，guardrail 禁止编造 evidence id，修复失败时回退到 deterministic report。

### 前端证据链展示

新增 `/imports` 评论导入工作台。已有报告详情页继续通过 `GET /api/reports/{report_id}/evidence` 展示引用证据和原始评论摘要。

## 当前边界

- CSV/JSON 导入当前处理请求体字符串，不做大文件分片上传。
- JSON-LD 适配是低风险 best-effort，不保证所有站点页面都能抽取。
- 真实 provider 调用和真实 token 成本不能用 mock 或 fixture 指标替代。
- 前端导入页先展示导入结果，后续可加“一键索引并生成报告”按钮。

## 后续优先级

1. 导入后自动触发 RAG indexing。
2. 导入后生成默认 RAG 评估集。
3. 从导入 task 一键生成 evidence-bound report。
4. 报告详情页将 evidence ref 锚点跳转到对应原始评论。
5. 为 CSV/JSON 大文件导入增加异步任务和进度事件。

