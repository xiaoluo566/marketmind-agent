# 模型与数据源决策

## 为什么现在必须定下来

Day 3 会开始设计数据库模型。模型、embedding、数据源、用户体系和项目隔离这些决策会影响字段、索引、任务模式和 API 契约。如果不提前固定，后续会在建表、写任务流和接前端时反复返工。

## 冻结结论

| 决策项 | 第一版选择 | 原因 |
| --- | --- | --- |
| 默认推理模型 | `gpt-5.4-mini` | 成本和延迟更适合开发、测试和多轮 Agent 调用 |
| 高质量报告模型 | `gpt-5.5` | 用于最终报告润色、复杂推理或面试演示时的高质量模式 |
| 模型提供方 | OpenAI-compatible | 代码层面保留兼容接口，避免绑定单一 SDK 封装 |
| embedding 模型 | `text-embedding-3-small` | 1536 维，成本低，足够支撑评论检索第一版 |
| embedding 维度 | `1536` | Day 3 的 pgvector 字段按 `vector(1536)` 设计 |
| 第一版主数据源 | Demo Dataset + CSV/JSON Upload | 保证主链路不被真实站点反爬、登录、验证码卡死 |
| 第一版 URL 爬虫 | Generic public page crawler | 只抓公开页面，作为能力展示，不绑定某个高风险电商站 |
| 用户体系 | 不做真实登录 | 使用默认本地用户/系统用户，数据库保留 `users` 扩展点 |
| 多项目隔离 | 数据库保留 `projects`，UI 第一版使用默认项目 | 先保留结构，不提前做复杂权限和项目管理 |

## 模型策略

第一版不要把最强模型作为所有步骤的默认模型。Agent 项目会频繁调用模型，如果每次 Thought、Action 参数生成、JSON 修复、报告生成都使用高成本模型，开发和测试成本会快速失控。

推荐分层：

- `MODEL_NAME=gpt-5.4-mini`：默认模型，用于任务规划、工具参数生成、普通总结、自修复。
- `REPORT_MODEL_NAME=gpt-5.5`：可选高质量模型，用于最终报告生成或重要演示。
- `MODEL_PROVIDER=openai-compatible`：代码层抽象为兼容 OpenAI API 形态的客户端。

后续如果模型不可用或成本过高，只改环境变量，不改数据库结构和业务流程。

## Embedding 策略

第一版固定：

```env
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

这样做的好处：

- pgvector 字段可以明确建成 `vector(1536)`。
- 成本比 `text-embedding-3-large` 更适合上千评论的开发测试。
- 召回质量足够支持“质量差、物流慢、退货、售后”等评论检索场景。

如果后续升级到 `text-embedding-3-large`，不能直接混写旧向量。必须新建 embedding 版本或重建索引，因为默认维度会变成 3072，除非显式使用 `dimensions` 参数压缩。

## 数据源策略

第一版按可靠性排序：

1. Demo Dataset：固定样例数据，保证开发、测试、演示稳定。
2. CSV/JSON Upload：用户手工导入评论和商品信息，作为真实站点失败时的兜底。
3. Generic URL Crawl：对公开网页做 best-effort 抽取，只作为采集能力展示。
4. Site Adapter：后续再选择低风险站点做定制适配器。

这样设计后，即使某个电商站临时封锁、页面变更或访问失败，系统仍然可以完整展示：任务创建、状态流转、数据清洗、RAG、Agent 分析、报告生成。

## CSV/JSON 第一版字段

第一版导入最小字段：

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `product_title` | 是 | string | 商品标题 |
| `review_content` | 是 | string | 评论正文 |
| `rating` | 否 | number | 评分，建议 1 到 5 |
| `source_url` | 否 | string | 来源页面 |
| `product_id` | 否 | string | 外部商品 ID |
| `review_id` | 否 | string | 外部评论 ID |
| `author_hash` | 否 | string | 匿名化用户标识 |
| `published_at` | 否 | string | 评论发布时间，ISO 8601 优先 |
| `price` | 否 | number | 商品价格 |
| `currency` | 否 | string | 货币，例如 `CNY`、`USD` |

导入规则：

- 没有 `review_id` 时由系统生成稳定 hash。
- 没有 `source_url` 时标记为 `manual_upload`。
- 不保存用户真实姓名、手机号、邮箱等隐私字段。
- 原始行数据保存在 `raw_payload`，便于排查和重跑。

## 用户与项目策略

第一版不做登录注册，不做复杂权限。

但数据库仍保留：

- `users`：创建一个默认本地用户，例如 `local-user`。
- `projects`：创建一个默认项目，例如 `default-project`。

这样做的原因是后续接多用户、多项目时不用大改主表关系；但前端第一版不展示复杂用户管理，避免偏离 Agent 主链路。

## 仍然暂不决定的内容

这些内容不会阻塞 Day 3，可以后置：

- 首个定制站点适配器选哪一个。
- 是否加入代理池。
- 是否接真实登录体系。
- 是否做多项目 UI。
- 是否把 report model 和 planner model 做成前端可配置。

## 与其他文档关系

- 数据表字段见 `data-model.md`
- embedding 检索见 `rag-memory.md`
- 爬虫边界见 `crawler-strategy.md`
- 环境变量见 `deployment.md` 和 `dev-environment.md`
- 待决事项收敛见 `open-questions.md`

