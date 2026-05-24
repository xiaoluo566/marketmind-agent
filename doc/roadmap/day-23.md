# Day 23 - 单元测试与校验测试

## 当天目标

先把最容易坏、最影响稳定性的逻辑用测试锁住：schema、状态转移、清洗、切片、报告结构。

## 前置依赖

- `day-22.md` 日志和错误码已整理
- 阅读 `../supporting/testing-strategy.md`
- 阅读 `../supporting/data-contract-examples.md`

## 当天交付物

- pytest 基础配置
- schema 测试
- 状态机测试
- RAG 切片测试
- 报告 schema 测试

## 实施步骤

1. 建立 `tests/` 目录
2. 写 Pydantic schema 正反样例
3. 测试 Agent step 状态转移
4. 测试评论清洗和切片
5. 测试报告必须带证据字段

## 验收标准

- 本地能运行测试命令
- 坏输入能被拒绝
- 核心状态转换有回归测试

## 风险与回退

- 不要为了测试而改坏真实业务约束
- 测试数据要小而稳定

## 关联文档

- 上一天：`day-22.md`
- 下一天：`day-24.md`
- 测试：`../supporting/testing-strategy.md`
- 数据契约：`../supporting/data-contract-examples.md`

## 建议提交

`test: cover core validators and state transitions`

