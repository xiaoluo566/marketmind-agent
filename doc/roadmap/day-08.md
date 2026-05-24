# Day 08 - 采集策略与反爬兜底

## 当天目标

把 Day 07 的“能抓”推进到“失败能解释、能兜底、能继续开发”。今天不追求突破风控，而是让采集层稳。

## 前置依赖

- `day-07.md` Playwright 最小采集已跑通
- 阅读 `../supporting/security-compliance.md`
- 阅读 `../supporting/risk-register.md`

## 当天交付物

- 限速策略
- 随机等待
- User-Agent 配置
- 失败截图
- CSV / JSON 手工导入兜底设计

## 实施步骤

1. 为 crawler 加入超时配置
2. 对页面加载和选择器等待做分阶段错误分类
3. 保存失败截图和失败 HTML
4. 设计手工导入数据格式
5. 把无法采集的任务标记为可恢复失败

## 验收标准

- 采集失败不会让任务无声卡住
- 失败事件包含 `error_code`
- 可以用手工数据继续走后续 RAG 和报告链路

## 风险与回退

- 不做绕过登录、验证码、付费墙的行为
- 如果目标站点失败率高，降低实时采集在演示中的权重

## 关联文档

- 上一天：`day-07.md`
- 下一天：`day-09.md`
- 风险：`../supporting/risk-register.md`
- 数据契约：`../supporting/data-contract-examples.md`

## 建议提交

`feat: harden crawler against flaky pages`

