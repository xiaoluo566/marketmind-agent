# MarketMind Agent

电商竞品调研与差评洞察 Agent 项目。

这个仓库先用于文档基线、开发规划和版本记录，后续再逐步落地 FastAPI、Celery、Playwright、PostgreSQL、pgvector、Streamlit/Next.js 等实现。

## 当前状态

- `doc/`：30 天开发计划 + 横向设计文档
- 本地 Git：即将初始化
- GitHub：待创建远程仓库并推送初始版本

## 开发原则

- 先做可跑通的闭环，再做规模化扩展
- 先保证可观测和可回退，再优化性能
- 所有长任务必须有状态持久化和失败恢复
- 所有 Agent 输出必须经过结构化校验

