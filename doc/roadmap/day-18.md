# Day 18 - 评论机会点评分与风险分析

## 当天目标

在 Day 17 证据链可回查的基础上，为报告增加可解释的风险与机会评分。评分必须绑定 evidence refs，必须能解释为什么高或低，必须在样本不足时降权。

Day 18 的重点不是预测销量，也不是输出“能不能爆款”的绝对结论，而是建立一套可测试的规则评分 baseline：让运营分析人员知道哪些维度风险更高、哪些痛点可能转化为产品机会。

## 前置依赖

- Day 15：`search_reviews_tool` 返回 evidence chunks。
- Day 16：`StructuredReport` 和 Markdown 输出可用。
- Day 17：`EvidenceChain` 和 `GET /api/reports/{report_id}/evidence` 可用。
- 支撑文档：
  - `../supporting/data-contract-examples.md`
  - `../supporting/testing-strategy.md`
  - `../supporting/interview-defense-dossier.md`
  - `../supporting/rag-memory.md`

## 设计边界

### Day 18 做什么

- 新增 `backend/app/reporting/scoring.py`。
- 定义 `ScorecardInput`。
- 定义 `DimensionScore`。
- 定义 `AnalysisScorecard`。
- 实现 `CompetitiveRiskScorer`。
- 实现 `attach_scorecard_to_report()`。
- `StructuredReport.to_markdown()` 增加“维度评分”章节。
- 新增 `tests/test_report_scoring.py`。

### Day 18 不做什么

- 不做机器学习评分模型。
- 不做销量预测。
- 不把分数包装成商业成功概率。
- 不接真实 LLM 打分。
- 不新增数据库字段或迁移。
- 不做前端评分图表。

## 评分维度

第一版维度：

| 维度 | key | 关键词示例 |
| --- | --- | --- |
| 质量风险 | `quality` | failed、broken、leak、defect、pump |
| 物流风险 | `logistics` | shipping、delivery、late、slow |
| 售后风险 | `support` | return、refund、support、service |
| 价格风险 | `price` | expensive、overpriced、value |
| 包装风险 | `packaging` | box、packaging、crushed、wet |
| 功能缺陷风险 | `functional_defect` | button、feature、not working |

关键词规则只是第一版 baseline。后续接真实 LLM 或分类模型时，必须保持输出 schema 不变。

## 评分输入

`ScorecardInput`：

- `task_id`
- `evidence_snippets`
- `minimum_samples`
- `metadata`

`evidence_snippets` 继续复用 Day 16 的 `EvidenceSnippet`，字段包括：

- `evidence_ref`
- `content`
- `similarity`
- `rating`
- `source_url`
- `metadata`

## 评分输出

`AnalysisScorecard`：

- `task_id`
- `status`
- `overall_risk_score`
- `overall_opportunity_score`
- `evidence_refs`
- `dimensions`
- `summary`
- `schema_version = scorecard.v1`
- `metadata`

`DimensionScore`：

- `dimension`
- `label`
- `risk_score`
- `opportunity_score`
- `evidence_refs`
- `sample_size`
- `average_rating`
- `max_similarity`
- `confidence`
- `sample_warning`
- `explanation`
- `metadata`

## 评分规则

第一版规则：

1. 根据关键词把 evidence snippets 分配到一个或多个维度。
2. 每个维度计算：
   - 样本数
   - 平均评分
   - 最大相似度
   - 置信度
3. 风险分由评分风险、相似度 boost 和样本 boost 组成。
4. 如果样本数低于 `minimum_samples`，按 `sample_size / minimum_samples` 降权。
5. 样本不足时写入 `sample_warning = LOW_SAMPLE_SIZE`。
6. 机会分基于风险分和置信度生成，用于表达“痛点是否可转化为改进机会”。
7. 无 evidence snippets 时返回 `insufficient_evidence`，不生成维度分。

## 报告展示

`attach_scorecard_to_report(report, scorecard)` 会返回一个新报告，把 scorecard 放入：

```text
StructuredReport.metadata.analysis_scorecard
```

`StructuredReport.to_markdown()` 会渲染：

- 综合风险分
- 综合机会分
- 各维度风险分
- 各维度机会分
- 置信度
- 样本数
- evidence refs
- explanation

## TDD 测试设计

新增 `tests/test_report_scoring.py`，覆盖：

1. 证据按维度分组，并绑定 evidence refs。
2. 高质量风险证据能得到较高风险分和机会分。
3. 样本不足时降权并写入 `LOW_SAMPLE_SIZE`。
4. 无证据时输出 `insufficient_evidence`，不编造分数。
5. `attach_scorecard_to_report()` 返回新报告，不原地修改旧报告。
6. Markdown 输出“维度评分”章节。

## 验收标准

- `uv run pytest tests\test_report_scoring.py` 通过。
- `uv run pytest tests\test_report_scoring.py tests\test_report_generation.py tests\test_report_evidence_chain.py` 通过。
- `uv run pytest` 全量通过。
- `uv run ruff check backend tests migrations` 通过。
- `uv run alembic heads` 仍然只有 `0002_task_queue_id (head)`。
- `cd frontend; npm run build` 通过。
- `doc/supporting/development-log.md` 和 `doc/supporting/interview-defense-dossier.md` 已更新。

## 风险与回退

### 风险 1：评分被误解为商业预测

规避方式：

- 文档明确评分只用于排序和解释。
- scorecard summary 明确“不代表严格商业预测”。
- 不输出“爆款概率”。

### 风险 2：小样本被过度解读

规避方式：

- `minimum_samples` 低于阈值时降权。
- 写入 `LOW_SAMPLE_SIZE`。
- explanation 明确样本不足。

### 风险 3：评分脱离证据

规避方式：

- 每个 `DimensionScore` 必须携带 `evidence_refs`。
- Markdown 展示每个维度的证据引用。
- 后续前端可以继续调用 Day 17 evidence chain API 回查来源。

## 当天选择思考

今天优先做评分规则，是因为 Day 16 和 Day 17 已经解决了报告结构和证据可追溯，但报告还只能“总结问题”，不能告诉用户“哪些问题更严重、哪些痛点更值得改进”。评分模块让报告从摘要进入分析。

我选择先做确定性规则评分，而不是接 LLM 或机器学习模型，是因为当前最需要的是可解释、可测试、可复现。关键词、评分、相似度和样本降权虽然简单，但每一步都能被测试和面试解释。

我暂时不把评分写入数据库新字段，是因为 Day 18 只是报告内容的一部分，放入 `StructuredReport.metadata.analysis_scorecard` 已经足够前端展示和后续导出。等后续要做报表筛选或跨任务统计，再考虑独立表或字段。

## 关联文档

- 上一天：`day-17.md`
- 下一天：`day-19.md`
- 数据契约：`../supporting/data-contract-examples.md`
- 测试策略：`../supporting/testing-strategy.md`
- 面试文档：`../supporting/interview-defense-dossier.md`
- 指标：`../supporting/llmops-metrics.md`

## 建议提交

`feat: 实现 Day 18 评论风险机会评分`
