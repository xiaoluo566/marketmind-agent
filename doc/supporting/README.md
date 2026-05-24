# Supporting 文档说明

这一组文档负责定义项目的长期约束，避免开发过程中只靠临时记忆做决定。

## 建议优先级

- 先看 `project-charter.md`，明确项目目标和非目标
- 再看 `market-positioning.md`，明确真实市场价值和不替代成熟卖家工具的边界
- 再看 `dependency-map.md`，知道哪些文档是前置，哪些是后置
- 再看 `architecture.md`、`data-model.md`、`api-contract.md`
- 再看 `model-and-data-decisions.md`，确认模型、embedding、数据源和用户边界
- 接着看 `agent-state-machine.md`、`prompt-strategy.md`、`crawler-strategy.md`、`rag-memory.md`
- 最后参考 `deployment.md`、`testing-strategy.md`、`risk-register.md`、`release-checklist.md`

## 交付和复盘

- `milestones-and-acceptance.md` 用来判断每周是否真的完成
- `market-positioning.md` 用来约束项目市场定位、用户价值和简历口径
- `llmops-metrics.md` 用来收集可写进简历的数据
- `demo-script.md` 用来准备最终展示
- `development-log.md` 用来实时记录 Day 1 到 Day 30 的实际开发过程和后续优化
- `future-iterations.md` 用来管理 30 天之后的增强点
- `dev-environment.md` 用来约束本机开发环境
- `ui-console-spec.md` 用来约束前端控制台行为
- `stitch-frontend-handoff.md` 用来约束 Stitch 生成前端的交接方式
- `stitch-generation-prompt.md` 用来保存可直接复制给 Stitch 的详细提示词
- `stitch-export-review.md` 用来记录 Stitch 导出内容的评审和 Next.js 重构方向
- `model-and-data-decisions.md` 用来集中记录模型、embedding、首发数据源、CSV/JSON schema、用户和项目隔离策略
