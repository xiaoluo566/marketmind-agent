# Day 09 - 采集结果入库

## 当天目标

把采集结果变成可复用的数据资产，而不是临时变量或控制台输出。后续 RAG、报告和证据链都依赖今天的入库结构。

## 前置依赖

- `day-08.md` 采集失败分类已设计
- 阅读 `../supporting/data-model.md`
- 阅读 `../supporting/crawler-strategy.md`

## 当天交付物

- 商品数据入库
- 评论数据入库
- 页面 artifact 入库
- source_url 和 task_id 关联
- 去重策略雏形

## 实施步骤

1. 把 crawler 输出转换成统一 schema
2. 写入 `products`
3. 写入 `reviews`
4. 保存截图、HTML、抽取文本到 `artifacts`
5. 记录每条数据的来源和采集时间

## 验收标准

- 采集结果能从数据库查回
- 每条评论能追到商品和任务
- 每个 artifact 能追到来源页面
- 重复运行不会造成不可控重复数据

## 实际完成记录

Day 9 完成了采集结果从“任务事件 payload”到“数据库资产”的推进。当前实现复用 Day 3 已经建好的表，不新增迁移：

- `products`：保存商品标题、价格、评分、来源 URL 和原始采集 payload。
- `crawled_pages`：保存页面来源、抽取文本、HTML artifact 引用和采集元数据。
- `artifacts`：保存 HTML 证据文件 URI、MIME、checksum 和 metadata。
- `reviews`：保存从页面中抽取到的评论内容、评分、外部评论 ID 和来源 URL。

实现上新增 `SQLAlchemyCrawlResultStore`，由 storage 层负责 ORM 写入和幂等更新。Worker 只在采集成功后调用持久化 store，不直接操作 ORM。

Day 9 同时补充了最小评论抽取能力：通用 HTML extractor 会识别 `class="review"`、`data-review-id`、`data-review` 或 `itemprop="review"` 这类结构，把评论转成 `CrawlReview`。

幂等策略第一版：

- 同一 `task_id + source_url` 复用同一个 `Product`。
- 同一 `task_id + source_url` 复用同一个 `CrawledPage`。
- 同一 `task_id + artifact_type + checksum` 复用同一个 `Artifact`。
- 评论优先使用页面提供的 `external_id`，缺失时根据 `task_id + product_id + source_url + content` 生成稳定 hash。

Day 9 刻意没有做的内容：

- 不新增复杂唯一索引，先在 service 层做幂等查询。
- 不做站点级评论区深度适配。
- 不做评论切片和 embedding，留到 Day 14。
- 不做 artifact 文件生命周期清理，后续进入运维和部署阶段补齐。

## 风险与回退

- 字段不稳定时先放入 `raw_payload`
- 不要为了少量字段过早重构复杂实体关系

## 关联文档

- 上一天：`day-08.md`
- 下一天：`day-10.md`
- 数据模型：`../supporting/data-model.md`
- RAG：`../supporting/rag-memory.md`

## 建议提交

`feat: persist crawl artifacts`
