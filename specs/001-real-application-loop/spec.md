# Feature Specification: 真实应用闭环

## User Scenarios

### US1 - 评论文件导入

作为电商运营用户，我希望提交 CSV/JSON 评论内容，让系统在不依赖高风险爬虫的情况下获得可分析的评论数据。

验收标准：

- 系统返回导入成功数量、重复数量、错误行数量和错误明细。
- 系统返回 `task_id` 和 `product_id`。
- 有效评论进入 `reviews`，后续可以被 RAG 索引。

### US2 - 低风险页面适配

作为开发者，我希望系统能读取公开页面中的 JSON-LD Product.review，作为低风险真实站点适配入口。

验收标准：

- 系统能从 `application/ld+json` 中提取 reviewBody、reviewRating 和 url。
- 系统不绕过登录、验证码、付费墙或安全策略。

### US3 - 前端导入和证据链展示

作为使用者，我希望在控制台提交评论内容，并看到导入结果，为后续报告证据链分析提供输入。

验收标准：

- 前端存在 `/imports` 页面。
- 页面文案为中文。
- 页面调用 `POST /api/imports/reviews`。
- 页面展示 `imported_count`、`duplicate_count`、`error_count` 和 `review_external_ids`。

## Functional Requirements

- FR1: 系统必须支持 CSV 评论导入。
- FR2: 系统必须支持 JSON 评论导入。
- FR3: 系统必须返回错误行报告，不因单行坏数据中断整批导入。
- FR4: 系统必须按 `review_id` 去重；缺失 `review_id` 时使用内容指纹。
- FR5: 系统必须把导入数据写入现有 `products`、`reviews`、`tasks`。
- FR6: 系统必须提供低风险 JSON-LD Product.review 解析。
- FR7: 系统必须提供前端中文导入工作台。
- FR8: 系统必须保持 evidence refs 约束，不能让 LLM 报告编造证据。

## Non-Goals

- 不做淘宝、京东等强反爬平台适配。
- 不做登录态采集。
- 不做大文件分片上传。
- 不把 mock 指标伪装成真实 provider 成本。

## Success Criteria

- CSV/JSON 导入契约测试通过。
- 导入后的评论可以被 `SQLAlchemyReviewChunkStore.index_task_reviews()` 索引。
- JSON-LD 评论适配器测试通过。
- 前端导入契约测试通过。
- RAG 质量、LLM prompt、报告证据链回归测试通过。

