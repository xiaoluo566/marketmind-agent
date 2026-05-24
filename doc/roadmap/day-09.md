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

