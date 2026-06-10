# 爬虫策略

## 第一版原则

- 只抓可公开访问内容
- 只做必要字段抽取
- 先稳定，再扩张站点覆盖
- 主链路优先支持 Demo Dataset 和 CSV/JSON Upload，真实 URL 采集不作为唯一演示入口

## 采集策略

- Playwright Async 为主
- requests 只用于简单静态页面
- 对复杂页面做 DOM 定位抽取
- 支持截图、HTML、文本三种证据格式

## 首发数据源策略

第一版不把某个大型电商站作为唯一入口。原因是页面结构、反爬、登录、验证码和地区访问差异都会影响演示稳定性。

优先级：

1. Demo Dataset：固定样例，服务开发、测试和面试演示。
2. CSV/JSON Upload：用户导入真实或半真实评论数据。
3. Generic public page crawler：对公开页面做 best-effort 抽取。
4. Site Adapter：后续再挑一个低风险站点做定制适配。

## 采集流水线

1. URL 校验
2. 站点适配器选择
3. 页面加载
4. DOM 等待
5. 字段抽取
6. 评论区抽取
7. 证据保存
8. 结果入库
9. 失败分类

## Adapter 设计

每个站点适配器只负责一个站点或一类页面结构。适配器应暴露：

- `can_handle(url)`
- `fetch_product_page(url)`
- `extract_product(html_or_page)`
- `extract_reviews(html_or_page)`
- `normalize_result(raw)`

## 证据保存

采集不是只保存最终字段，还要保存能复盘的证据：

- 页面截图
- 原始 HTML
- 抽取后的文本
- source url
- 采集时间
- 失败截图

Day 8 实现状态：

- 已支持成功 HTML artifact 本地保存。
- 已支持解析失败 / 访问拦截时的失败 HTML artifact 本地保存。
- artifact 引用已进入任务事件 payload。
- 截图证据留到后续实现。

Day 9 实现状态：

- 成功采集结果已写入 `products`、`crawled_pages`、`reviews` 和 `artifacts`。
- `crawl completed` 事件会携带持久化后的 `product_id`、`page_id`、`artifact_ids` 和 `review_ids`。
- 第一版评论抽取只处理简单 review 容器，复杂站点评论区仍留给后续 adapter。

## 风控策略

- 限速
- 随机等待
- 重试退避
- 失败回退到手工导入
- 记录被拦截的页面特征

## 抽取目标

- 标题
- 价格
- 评论摘要
- 评分
- 售后信息
- 页面来源

## 边界

- 不做违法绕过
- 不做账号破解
- 不做侵入式采集
- 不绕过登录、验证码、付费墙或网站安全策略

## 失败分类

- `PAGE_TIMEOUT`
- `DOM_NOT_FOUND`
- `ACCESS_BLOCKED`
- `NETWORK_ERROR`
- `PARSER_ERROR`
- `UNKNOWN_SITE`

## 与其他文档关系

- 采集数据入库见 `data-model.md`
- 数据源冻结见 `model-and-data-decisions.md`
- 失败处理见 `risk-register.md`
- RAG 消费采集结果见 `rag-memory.md`

## 真实应用闭环适配器补充

当前低风险真实站点适配选择 JSON-LD `Product.review`：

- 只读取公开 HTML 中的 `application/ld+json`。
- 支持从 `reviewBody`、`reviewRating.ratingValue`、`url` 中提取评论正文、评分和来源。
- 适用于公开独立站、Shopify 风格商品页和本地 HTML fixture。
- 不绕过登录、验证码、付费墙或安全策略。

该适配器的定位是“真实公开页面结构支持”，不是强反爬突破。若页面没有 JSON-LD 评论，系统仍回退到 generic HTML review 容器抽取或手动 CSV/JSON 导入。
