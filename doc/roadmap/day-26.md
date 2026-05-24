# Day 26 - 版本管理与 CI

## 当天目标

让每次提交都更可靠，并且未来可以方便回退。今天要把 GitHub 仓库从代码存储升级成开发流程工具。

## 前置依赖

- `day-25.md` Docker Compose 基础可用
- 阅读 `../supporting/change-management.md`
- 阅读 `../supporting/release-checklist.md`

## 当天交付物

- 分支策略落地
- Git tag 规则
- CI 草案或基础 workflow
- PR 检查清单

## 实施步骤

1. 确认 `main` 只保留稳定版本
2. 创建 `dev` 分支
3. 写 GitHub Actions 草案：lint、test、类型检查
4. 定义 release tag 命名
5. 在 README 写明贡献和回退方式

## 验收标准

- 每个版本能对应到 commit
- 测试失败不应进入稳定分支
- 发版前有 checklist

## 风险与回退

- 不要引入过重 CI 导致开发变慢
- 如果 CI 暂时无法跑完整环境，先跑单元测试

## 关联文档

- 上一天：`day-25.md`
- 下一天：`day-27.md`
- 变更管理：`../supporting/change-management.md`
- 发版：`../supporting/release-checklist.md`

## 建议提交

`chore: establish release workflow`

