# 开发流程

## 每日流程

1. 先读当天 `doc/roadmap/day-xx.md`
2. 确认输入依赖是否满足
3. 创建小范围任务分支
4. 先写测试或验收脚本
5. 实现最小功能
6. 本地验证
7. 提交小步 commit
8. 更新 bug / research / open questions 文档

## 开工前检查

- 当前分支是否正确
- 工作区是否干净
- 前一天的验收项是否完成
- 当天文档的前置文档是否读过
- 是否需要新增数据库迁移
- 是否需要新增测试数据

## 分支策略

- `main`：稳定版本，只合入可演示状态
- `dev`：日常集成分支
- `feature/day-xx-topic`：当天功能分支
- `hotfix/topic`：修复已知问题

## 提交建议

- `docs:` 文档
- `feat:` 新功能
- `fix:` 修复
- `test:` 测试
- `refactor:` 重构
- `chore:` 工程配置
- `perf:` 性能优化

## 回退要求

- 每天至少一个可回退点
- 每周打一个里程碑 tag
- 数据库迁移必须能说明回滚方式

## 文档更新规则

- 改 API 前先改 `api-contract.md`
- 改数据表前先改 `data-model.md`
- 改 Agent 流程前先改 `agent-state-machine.md`
- 改 prompt 前先改 `prompt-strategy.md`
- 改部署方式前先改 `deployment.md`

## 与其他文档关系

- 里程碑见 `milestones-and-acceptance.md`
- 发版见 `release-checklist.md`
- 风险见 `risk-register.md`
