# 第二阶段发布候选：v0.2-phase2-rc1

## 文档定位

这份文档记录 Day31-Day40 的 Phase 2 RC 收口结果。它不是最终产品发布说明，而是一个可审计的阶段边界：哪些能力已经有代码和测试，哪些能力只是规划，哪些能力仍然受环境或真实 provider 限制。

建议候选 tag：

```text
v0.2-phase2-rc1
```

## Phase 2 RC 范围

本阶段覆盖 Day31-Day39 的深化内容：

- Day31：前端中文化基线，保持 API 字段和技术 ID 不翻译。
- Day32：前端失败任务 retry 入口。
- Day33：retry/recovery 前后端链路联调与恢复事件验收。
- Day34：embedding provider 配置、错误分类和 OpenAI-compatible 接入边界。
- Day35：RAG 质量评估 fixture 和 provider metrics baseline。
- Day36：真实 LLM 报告 prompt 契约、evidence refs 约束和 JSON repair。
- Day37：Playwright mock E2E 主链路。
- Day38：Markdown 报告导出和 JSON evidence package。
- Day39：LLMOps summary API 和中文指标面板。
- Day40：Phase 2 RC 审计、文档同步、测试门禁和前端离线构建缺口修复。

## main 合并判断

可以合并 `main` 的条件：

- `dev` 上 Day31-Day40 相关提交全部通过本地验证。
- `uv run pytest`、ruff、前端 lint/build/audit 至少在本地通过。
- README、roadmap、development log、testing strategy、interview dossier 和 release checklist 已同步。
- 文档明确写出未完成项，不声明 v1.0。

不建议合并 `main` 的情况：

- 任一核心测试失败。
- 前端 `npm run build` 仍依赖外部网络或本地缓存。
- 文档把 mock、fixture 或 database_snapshot 指标写成真实生产数据。
- 仍有未解释的数据库迁移、Docker volume 或分支历史风险。

## 诚实边界

本 RC 不声明 v1.0，也不声明真实生产数据。

当前不能声明完成的内容：

- Docker Compose 真实 build/up：目前只把 compose 配置和 Dockerfile 纳入测试，真实 `docker compose up --build` 仍依赖 Docker Desktop daemon。
- 真实 provider 成本：Day39 的 LLMOps summary 能显示 `agent_runs.total_cost` 字段，但没有真实 provider 账单和持久化采样时，不写真实线上成本。
- 真实线上 RAG 准确率：Day35 是 fixture 评估集，不等同真实业务标注集。
- 真实多容器 E2E：Day37 是 mock dev server 下的 Playwright E2E，不等同 Docker/API/Redis/Celery/provider 全链路。
- branch protection：当前文档要求配置 required checks，但没有在 GitHub 仓库中自动完成配置。

## Day40 修复记录

Day40 验收时发现前端生产构建依赖 `next/font/google` 拉取 Google Fonts。这个设计会让 `npm run build` 在无外网或受限网络下失败。

处理方式：

- 移除 `frontend/src/app/layout.tsx` 中的 `next/font/google`。
- 在 `frontend/src/app/globals.css` 中改用系统字体栈。
- 在 `tests/test_frontend_localization_contract.py` 中补回归测试，禁止根布局重新引入 `next/font/google`。

这属于已修复缺口，不阻塞 Phase 2 RC。

## 回退方案

如果合并后发现问题：

- 小范围代码问题：优先 `git revert <commit>`。
- 前端构建问题：回退 Day40 字体变更或保留系统字体栈重新修复。
- 文档边界错误：直接补文档提交，不改动业务代码。
- 多提交阶段问题：从 `v0.2-phase2-rc1` 或合并前 dev 提交创建修复分支。

## 下一阶段承接

Phase 2 RC 后，项目应优先补真实应用闭环，而不是继续堆 Agent 概念：

- CSV/JSON 评论导入。
- 低风险真实站点适配器。
- 评论分析质量评估。
- 真实 LLM 报告，但必须保持 evidence refs 约束。
- 前端展示“结论 -> 引用证据 -> 原始评论”的证据链报告。
