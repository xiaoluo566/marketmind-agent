# MarketMind Agent

电商竞品调研与差评洞察 Agent 项目。

这个仓库用于开发 FastAPI + Celery + PostgreSQL/pgvector + Playwright + Next.js 的电商竞品调研 Agent 系统。

## 当前状态

- `doc/`：30 天开发计划 + 横向设计文档
- `backend/`：FastAPI 后端骨架
- `frontend/`：Next.js 控制台骨架
- `stitch_marketmind_control_center/`：本地 Stitch 原始设计导出，已被 `.gitignore` 忽略，只作为可选视觉参考
- 本地 Git：已初始化
- GitHub：私有仓库已创建并已推送初始版本
- 分支策略：`main` 保持稳定演示版本，`dev` 用于 Day 2 以后日常开发

## 阅读顺序

1. [doc/README.md](doc/README.md)
2. [doc/supporting/project-charter.md](doc/supporting/project-charter.md)
3. [doc/supporting/dependency-map.md](doc/supporting/dependency-map.md)
4. [doc/supporting/architecture.md](doc/supporting/architecture.md)
5. [doc/supporting/data-model.md](doc/supporting/data-model.md)
6. [doc/roadmap/30-day-master-plan.md](doc/roadmap/30-day-master-plan.md)

## 项目定位

这不是一个单纯的爬虫项目，也不是一个只会聊天的 Agent demo。它要做的是把“采集、分析、决策、报告、回退、复盘”串成一个能持续迭代的工程系统。

## 当前阶段

现在处于“架构冻结 + 基础骨架”阶段。Day 1 已完成仓库、文档、FastAPI health 和 Next.js 控制台骨架；Day 2 开始在 `dev` 分支上冻结架构边界，再继续接数据库、任务队列和真实任务流。

## 开发原则

- 先做可跑通的闭环，再做规模化扩展
- 先保证可观测和可回退，再优化性能
- 所有长任务必须有状态持久化和失败恢复
- 所有 Agent 输出必须经过结构化校验
- 所有新功能都要能落到对应的文档和验收标准上

## 版本策略

- `main`：可演示、可回退、可打标签的稳定版本
- `dev`：日常开发汇总分支
- `feature/*`：短周期功能分支
- 每个里程碑都保留 Git tag 和 GitHub 版本记录
