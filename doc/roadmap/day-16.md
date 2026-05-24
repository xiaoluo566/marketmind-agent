# Day 16 - 报告生成骨架

## 当天目标

把 Agent 的观察和检索证据变成结构化报告。今天先做报告结构，不追求文案华丽。

## 前置依赖

- `day-15.md` 差评搜索工具可用
- 阅读 `../supporting/prompt-strategy.md`
- 阅读 `../supporting/data-contract-examples.md`

## 当天交付物

- 报告 schema
- 报告生成 prompt
- 报告入库逻辑
- Markdown 输出草案

## 实施步骤

1. 定义报告章节：摘要、竞品概况、用户痛点、机会点、风险、证据
2. 定义报告 Pydantic schema
3. 把 Agent observations 和 RAG 证据作为输入
4. 生成报告后先校验再入库
5. 输出 Markdown 版本用于前端展示

## 验收标准

- 报告结构稳定
- 关键结论能绑定证据 ID
- 报告生成失败会记录错误

## 风险与回退

- 不要让模型直接生成没有 schema 的长文本
- 如果报告太空，回到 RAG 检索补证据

## 关联文档

- 上一天：`day-15.md`
- 下一天：`day-17.md`
- Prompt：`../supporting/prompt-strategy.md`
- 简历：`../supporting/resume-story.md`

## 建议提交

`feat: generate structured reports`

