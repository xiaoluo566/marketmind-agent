# 待决问题

## 当前待定

- 首个定制站点适配器选哪一个
- 是否加入代理池
- 是否把 report model 和 planner model 做成前端可配置

## 建议优先决策

1. Day 8 前决定首个定制站点适配器
2. Day 8 前决定是否需要代理池
3. Day 16 前决定最终报告是否开放模型切换

## 已决策

- 正式前端使用 Next.js
- Stitch 导出作为设计参考
- 后端、任务系统、数据库、Agent、RAG 和部署由本仓库实现
- 第一版前端通过 FastAPI API 契约接入，不直接访问数据库或模型
- 第一版允许 CSV / JSON 作为爬虫失败时的兜底数据源
- 第一版采用“模块化单体 + Celery worker”，暂不拆复杂微服务
- Day 2 以后日常开发使用 `dev` 分支，`main` 保持稳定可演示版本
- 默认推理模型使用 `gpt-5.4-mini`
- 高质量报告模型预留 `gpt-5.5`
- embedding 使用 `text-embedding-3-small`，维度固定为 1536
- 第一版主数据源使用 Demo Dataset + CSV/JSON Upload
- URL 爬虫第一版使用 generic public page crawler，不绑定高风险电商站
- 第一版不做真实登录，使用默认本地用户
- 第一版数据库保留 `projects`，前端只使用默认项目

## 决策原则

如果一个问题会影响数据库、API 或任务状态机，必须先决定。

如果一个问题只影响 UI 样式或报告文案，可以后置。

## 原则

- 没决定的内容先不要写死到代码
- 有分歧先进入调研记录
- 影响架构的事项先定边界再实现

## 与其他文档关系

- 技术决策进入 `tech-stack-decisions.md`
- 模型和数据源决策进入 `model-and-data-decisions.md`
- 风险进入 `risk-register.md`
- 后续增强进入 `future-iterations.md`
