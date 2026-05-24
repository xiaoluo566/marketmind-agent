# Prompt 策略

## 为什么要单独写

Agent 项目最后最容易失控的地方，不是 API，而是 prompt：版本一多，行为就会漂移，最后没人知道是哪一版 prompt 让系统变聪明或者变坏了。

## Prompt 类型

- `system prompt`：定义 Agent 身份、边界和优先级
- `tool prompt`：定义工具如何被调用
- `extraction prompt`：定义如何抽取结构化信息
- `summary prompt`：定义如何压缩长上下文
- `report prompt`：定义如何生成报告
- `self-heal prompt`：定义 JSON 修复和格式恢复

## 每个 prompt 必须带的元信息

- 名称
- 版本号
- 适用场景
- 输入类型
- 输出 schema
- 失败案例
- 回归样例

## 版本管理建议

- prompt 不要直接散落在代码里
- 每个阶段只维护少量稳定模板
- prompt 调整必须记录原因和样例

## 与其他文档关系

- `agent-state-machine.md` 决定 prompt 在什么时候被调用
- `data-model.md` 决定 prompt 产出的数据怎么存
- `testing-strategy.md` 决定 prompt 是否回归

