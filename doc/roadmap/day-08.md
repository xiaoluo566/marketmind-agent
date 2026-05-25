# Day 08 - Playwright 最小采集与失败兜底

## 当天目标

在 Day 7 完成基础设施联调和任务事件持久化之后，开始接入采集层。今天只要求 Playwright Async 跑通一个目标页面或本地 HTML fixture 的最小采集，不追求多站点覆盖。

Day 8 的成果是让任务链路第一次拿到“外部页面证据”：标题、价格、核心文本、截图或 HTML。采集失败也必须能解释，不能让任务无声卡住。

## 前置依赖

- `day-07.md` 第一周联调和任务事件持久化已完成
- 阅读 `../supporting/crawler-strategy.md`
- 阅读 `../supporting/security-compliance.md`
- 阅读 `../supporting/risk-register.md`
- Playwright 浏览器依赖可安装或已安装

## 当天交付物

- crawler service 目录
- Playwright browser/context/page 生命周期封装
- 一个最小采集函数
- 标题、价格或核心文本抽取
- 成功截图或 HTML 证据保存接口
- 失败截图或失败 HTML 保存接口
- 采集失败错误分类雏形
- CSV / JSON 手工导入兜底设计

## 实施步骤

1. 建立 `backend/app/crawler/` 目录，拆分 browser、extractor、schemas。
2. 实现 Playwright Async 页面加载函数。
3. 先支持本地 HTML fixture，再支持公开 URL best-effort 采集。
4. 抽取少量稳定字段，不追求复杂站点适配。
5. 为页面加载、超时、选择器缺失、反爬拦截分别定义错误类型。
6. 保存成功截图、原始 HTML 或抽取文本，作为后续证据链基础。
7. 采集成功或失败时写入任务事件，确保前端能看到采集阶段进度。
8. 设计 CSV / JSON 导入格式，作为真实网站采集失败时的兜底入口。

## 验收标准

- 能从本地 fixture 或一个公开页面抽取至少 2 个字段。
- 采集结果能关联 `task_id`。
- 成功事件包含可追溯的证据信息。
- 失败事件包含 `error_code` 和简短原因。
- 采集失败不会让任务一直停在 `running`。
- 不绕过登录、验证码、付费墙或其他访问限制。

## 风险与回退

- 如果目标站点不稳定，先使用本地 HTML fixture 保证主链路开发。
- 如果 Playwright 浏览器安装失败，先完成接口、schema 和 fixture 测试。
- 不做复杂代理池，不做验证码绕过，不做登录态采集。
- 如果真实页面结构变化，采集层必须返回可解释失败，而不是吞掉异常。

## 关联文档

- 上一天：`day-07.md`
- 下一天：`day-09.md`
- 爬虫策略：`../supporting/crawler-strategy.md`
- 安全合规：`../supporting/security-compliance.md`
- 风险：`../supporting/risk-register.md`
- 数据契约：`../supporting/data-contract-examples.md`

## 建议提交

`feat: 接入 Playwright 最小采集`
