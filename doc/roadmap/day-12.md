# Day 12 - 结构化输出与自愈

## 当天目标

降低模型输出不符合 schema 的失败率。所有 Agent 输出都必须先校验，再进入业务流程。

## 前置依赖

- `day-11.md` ReAct loop 可运行
- 阅读 `../supporting/prompt-strategy.md`
- 阅读 `../supporting/security-compliance.md`

## 当天交付物

- Pydantic 输出模型
- Tenacity 重试策略
- JSON 修复 prompt
- 校验失败日志
- 自修复结果统计字段

## 实施步骤

1. 定义工具选择输出 schema
2. 定义报告结构 schema
3. 对模型返回先做 JSON parse
4. parse 失败时触发 self-heal prompt
5. self-heal 仍失败时写入结构化错误
6. 把失败样例保存为后续测试数据

## 验收标准

- 非标准 JSON 不会直接进入业务逻辑
- 自修复次数被记录
- 失败时能看到原始输出和错误原因
- 至少有一个回归测试覆盖坏 JSON

## 风险与回退

- 不要无限重试模型
- 不要让自修复 prompt 改变业务含义
- 如果模型不稳定，先降低输出复杂度

## 关联文档

- 上一天：`day-11.md`
- 下一天：`day-13.md`
- Prompt：`../supporting/prompt-strategy.md`
- LLMOps：`../supporting/llmops-metrics.md`

## 建议提交

`feat: add structured output guardrails`

