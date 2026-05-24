# Day 01 - 项目定调与仓库骨架

## 当天目标

把项目从一个想法变成可以持续开发、可以回退、可以复盘的工程仓库。今天不写业务代码，重点是把范围、目录、文档入口、版本策略和开发纪律固定下来。

## 前置依赖

- 阅读 `../supporting/project-charter.md`
- 阅读 `../supporting/dependency-map.md`
- 确认 GitHub 私有仓库可访问

## 当天交付物

- 项目 README
- `doc/` 文档入口
- `supporting/` 横向文档目录
- `roadmap/` 30 天开发目录
- `.gitignore`
- 首个 Git 提交

## 实施步骤

1. 创建仓库基础文件：`README.md`、`.gitignore`、`doc/README.md`
2. 明确项目名称、目标用户、核心能力和非目标
3. 写清楚“为什么不是普通爬虫，也不是普通聊天机器人”
4. 初始化本地 Git 仓库并提交文档基线
5. 创建 GitHub 私有仓库并推送 `main`

## 验收标准

- 打开仓库能理解项目目标
- 打开 `doc/README.md` 能找到后续所有文档
- GitHub 仓库是私有仓库
- `main` 分支有第一次提交

## 风险与回退

- 如果 GitHub 创建失败，先保证本地 Git 提交存在
- 如果项目范围过大，立刻写入 `../supporting/open-questions.md`

## 关联文档

- 下一天：`day-02.md`
- 总计划：`30-day-master-plan.md`
- 变更管理：`../supporting/change-management.md`

## 建议提交

`docs: initialize project charter and roadmap`

