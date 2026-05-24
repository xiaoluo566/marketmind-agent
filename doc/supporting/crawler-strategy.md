# 爬虫策略

## 第一版原则

- 只抓可公开访问内容
- 只做必要字段抽取
- 先稳定，再扩张站点覆盖

## 采集策略

- Playwright Async 为主
- requests 只用于简单静态页面
- 对复杂页面做 DOM 定位抽取
- 支持截图、HTML、文本三种证据格式

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

## 失败分类

- `PAGE_TIMEOUT`
- `DOM_NOT_FOUND`
- `ACCESS_BLOCKED`
- `NETWORK_ERROR`
- `PARSER_ERROR`
- `UNKNOWN_SITE`

## 与其他文档关系

- 采集数据入库见 `data-model.md`
- 失败处理见 `risk-register.md`
- RAG 消费采集结果见 `rag-memory.md`
