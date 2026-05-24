# 文档依赖图

## 读法

这份地图不是形式主义，它的作用是避免开发时顺序错乱。前面的文档定义“边界和契约”，后面的文档才进入实现。

## 主链路

1. `project-charter.md`
2. `architecture.md`
3. `data-model.md`
4. `api-contract.md`
5. `agent-state-machine.md`
6. `prompt-strategy.md`
7. `crawler-strategy.md`
8. `rag-memory.md`
9. `ui-console-spec.md`
10. `testing-strategy.md`
11. `deployment.md`
12. `release-checklist.md`

## 关系说明

| 文档 | 依赖 | 作用 |
| --- | --- | --- |
| `project-charter.md` | 无 | 定义项目要解决的问题和边界 |
| `architecture.md` | `project-charter.md` | 定义系统如何拆层 |
| `data-model.md` | `architecture.md` | 把架构落成数据表与关系 |
| `api-contract.md` | `architecture.md`、`data-model.md` | 固定服务之间的输入输出 |
| `agent-state-machine.md` | `api-contract.md`、`data-model.md` | 固定 Agent 执行流程和落库方式 |
| `prompt-strategy.md` | `agent-state-machine.md` | 定义 prompt 如何版本化和测试 |
| `crawler-strategy.md` | `architecture.md`、`api-contract.md` | 定义采集层如何稳定工作 |
| `rag-memory.md` | `data-model.md`、`crawler-strategy.md` | 定义评论如何变成可检索知识 |
| `ui-console-spec.md` | `api-contract.md` | 定义控制台如何展示任务和报告 |
| `testing-strategy.md` | 全部前置文档 | 定义如何验证整个系统 |
| `deployment.md` | `data-model.md`、`testing-strategy.md` | 定义如何部署和回退 |
| `release-checklist.md` | `deployment.md`、`testing-strategy.md` | 定义发版前最后检查 |

## 交叉引用建议

- 如果你在改 API，先看 `api-contract.md`，再看 `agent-state-machine.md`
- 如果你在改爬虫，先看 `crawler-strategy.md`，再看 `rag-memory.md`
- 如果你在改报告逻辑，先看 `rag-memory.md`、`prompt-strategy.md`、`ui-console-spec.md`
- 如果你在准备发版，先看 `testing-strategy.md`、`deployment.md`、`release-checklist.md`

