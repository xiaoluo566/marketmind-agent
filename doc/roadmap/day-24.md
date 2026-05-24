# Day 24 - 集成测试与回归样例

## 当天目标

验证主链路不是各模块单独能跑，而是能连起来跑：提交任务、Worker 执行、写状态、生成报告。

## 前置依赖

- `day-23.md` 单元测试基础已建立
- 阅读 `../supporting/testing-strategy.md`
- Docker 或本地数据库可用

## 当天交付物

- API + DB 集成测试
- Celery 任务投递测试
- 报告生成集成测试
- 固定 HTML / CSV fixture

## 实施步骤

1. 准备测试数据库
2. 写 `POST /api/tasks` 集成测试
3. 写 Worker 消费测试
4. 用 fixture 跑采集和报告流程
5. 保存已知 bug 的回归样例

## 验收标准

- 主链路测试能本地跑通
- 测试失败能指向具体模块
- fixture 不依赖不稳定外部网站

## 风险与回退

- 不要让集成测试依赖真实大模型每次调用
- 模型和爬虫可以用 mock 或固定样例隔离

## 关联文档

- 上一天：`day-23.md`
- 下一天：`day-25.md`
- 部署：`../supporting/deployment.md`
- 发版：`../supporting/release-checklist.md`

## 建议提交

`test: add integration coverage`

