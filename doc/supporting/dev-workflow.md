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

