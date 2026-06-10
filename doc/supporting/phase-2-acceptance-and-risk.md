# 第二阶段验收与风险控制

## 文档定位

这份文档定义第二阶段每个能力的验收门槛、风险、回退策略和分支策略。它和 `phase-2-practicality-plan.md` 配套：前者说明做什么，本文说明做到什么程度才算完成。

关联文档：

- `../roadmap/phase-2-master-plan.md`
- `../roadmap/day-31.md`
- `frontend-localization-contract.md`
- `release-checklist.md`
- `rollback-runbook.md`
- `testing-strategy.md`

## 总体验收门槛

第二阶段每个开发项必须满足：

- 文档先写。
- 测试先写或同步补充。
- 本地门禁通过。
- 开发日志更新。
- 面试防守手册更新。
- 不夸大未验证能力。
- main 只保留稳定版本。

## 分支策略

- `main`：只保留稳定版本和已通过 CI 的阶段结果。
- `dev`：第二阶段日常开发。
- 大功能可以从 `dev` 拆临时分支，例如 `feature/day31-localization`，但合并前仍回到 `dev` 验证。

main 只保留稳定版本。这一点在第二阶段更重要，因为后续会接真实 provider、真实 Docker 和 E2E，失败概率会比文档阶段更高。

## 风险清单

| 风险 | 影响 | 控制方式 | 回退策略 |
| --- | --- | --- | --- |
| 中文界面撑坏布局 | 页面观感下降 | 先测核心页面，必要时缩短文案 | 回退单个组件文案或样式 |
| 误翻译 API 字段名 | 前后端契约破坏 | 契约测试禁止翻译字段名 | revert 对应组件改动 |
| 前端 retry 重复点击 | 多次投递同一任务 | 按钮 loading 和后端 retry 限制 | 禁用按钮并保留后端保护 |
| Docker daemon 不可用 | 无法真实 compose build/up | 继续只声明 compose config | 记录为未补验，不阻塞其他功能 |
| 真实 provider 超时 | RAG 或报告中断 | provider timeout、retry、错误分类 | 切回 fake provider 或关闭真实 provider |
| LLM 输出坏 JSON | 报告生成失败 | Guardrails 和 self-heal | 输出证据不足报告或结构化错误 |
| E2E flaky | CI 不稳定 | 先本地稳定，再进入 CI | 把 E2E job 设为独立阶段 |

Day37 已完成本地 mock 模式 Playwright E2E 主流程，`npm run test:e2e` 通过。当前风险从“没有浏览器 E2E”调整为“E2E 尚未作为 CI required check 且尚未覆盖真实 Docker/API/provider 全链路”。

## Docker daemon 不可用时的处理

Docker daemon 不可用不是代码失败，但必须诚实记录。

允许声明：

- `docker compose config` 已验证。
- Dockerfile 和 compose 契约测试已通过。

不允许声明：

- 真实 `docker compose build` 已完成。
- 真实 `docker compose up` 已完成。
- 容器内 worker 消费已完成。

一旦 Docker Desktop daemon 可用，需要补跑：

```powershell
docker compose up --build
curl http://localhost:8000/api/health
```

然后提交补验记录。

## 中文界面验收

Day31 中文界面完成标准：

- 核心导航、标题、表单、按钮、状态提示为中文。
- API 字段名、枚举值、trace id、task id、report id 保持英文技术标识。
- `npm run lint` 和 `npm run build` 通过。
- `tests/test_frontend_localization_contract.py` 通过。

## Retry 前端验收

Retry 前端完成标准：

- failed 任务展示 `重试任务`。
- 非 failed 任务不展示 retry。
- 点击后调用 `POST /api/tasks/{task_id}/retry`。
- 成功后刷新任务状态和事件流。
- 失败时展示错误码和用户可读原因。

Day33 补充验收：

- Day33 已确认 mock 浏览器层可以完成 `重试任务 -> 重试任务已提交 -> 排队中 -> task.retry_submitted`。
- Day33 已确认后端单进程测试覆盖 `task waiting retry`、`task requeued` 和 `task recovery resumed`。
- Day33 已在前端展示层把真实后端 retry/recovery message 映射为中文说明。
- Day33 未声明真实 Redis/Celery 容器链路通过，因为 Docker daemon 仍不可用。

Day33 仍未完成：

- 真实 `docker compose up`。
- 容器内 Worker 消费 recovery payload。
- 真实容器链路恢复成功率统计。

## Provider 验收

真实 provider 完成标准：

- 配置缺失时 fail fast。
- fake provider 仍保留给测试。
- 输出维度校验。
- latency / token / cost 指标记录。
- provider 错误写入错误分类。

## 回退策略

优先级：

1. 小范围 UI 文案错误：改回单个组件。
2. 前端功能错误：revert 对应提交。
3. provider 错误：关闭 provider 配置，回到 fake provider。
4. Docker 错误：保留 compose config 验证，不声明真实启动。
5. 已推送远程问题：优先 `git revert`，不使用 `git reset --hard` 改写历史。

## 第二阶段结束条件

第二阶段不需要一次性完成所有 backlog。阶段结束可以定义为：

- 中文界面完成。
- retry 前端闭环完成。
- 至少一个真实 provider 或真实 compose 补验完成。
- Playwright E2E 覆盖主流程。Day37 已完成 mock dev server 主链路，真实 API E2E 仍属于后续增强。
- main 分支保持稳定且 CI 通过。
