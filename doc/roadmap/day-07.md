# Day 07 - Playwright 爬虫骨架

## 当天目标

用 Playwright Async 跑通一个页面的采集，不追求覆盖多个站点。今天的成果是采集层最小闭环。

## 前置依赖

- `day-06.md` 任务状态可记录
- 阅读 `../supporting/crawler-strategy.md`
- Playwright 浏览器依赖已安装

## 当天交付物

- crawler 模块
- 页面加载函数
- 标题、价格或核心文本抽取
- 页面截图保存
- 采集失败分类雏形

## 实施步骤

1. 建立 crawler service 目录
2. 实现 Playwright browser/context/page 生命周期
3. 加载目标页面并等待关键选择器
4. 抽取少量稳定字段
5. 保存截图和 HTML，作为后续证据

## 验收标准

- 能从一个目标页面抽取至少 2 个字段
- 页面失败时能记录错误类型
- 采集结果能关联 `task_id`

## 风险与回退

- 如果目标站点不稳定，先使用本地 HTML fixture
- 不要过早做复杂反爬

## 关联文档

- 上一天：`day-06.md`
- 下一天：`day-08.md`
- 爬虫策略：`../supporting/crawler-strategy.md`
- 安全合规：`../supporting/security-compliance.md`

## 建议提交

`feat: bootstrap playwright crawler`

