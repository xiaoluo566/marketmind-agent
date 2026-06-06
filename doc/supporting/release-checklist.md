# 发版检查清单

## 发版前

- 核心测试通过
- 数据迁移脚本可执行
- `.env.example` 已更新
- README 与文档入口已同步
- 阶段审计文档已更新
- 关键指标已记录

## 发版时

- 创建 Git tag
- 记录提交号
- 保存回退分支
- 确认 GitHub 仓库状态

## 发版后

- 跑一次完整演示
- 记录异常和修复
- 更新 `bug-log-template.md`
- 更新 `llmops-metrics.md`

## 与其他文档关系

发版前要同时看 `testing-strategy.md`、`deployment.md`、`milestones-and-acceptance.md`、`demo-script.md`。
