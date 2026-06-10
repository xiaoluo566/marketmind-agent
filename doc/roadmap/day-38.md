# Day 38 - 报告导出与证据包

## 当天目标

Day38 的目标是让报告从“页面里能看”升级为“可以交付给别人”。对电商运营场景来说，用户最终需要的是可保存、可分享、可复盘的报告交付物，而不只是控制台页面。

当天重点是实现 Markdown 报告导出、JSON evidence package、前端报告详情下载入口和导出脱敏边界。PDF 暂不做，避免把排版复杂度提前引入。

## SDD 检查记录

用户目标：

- 运营用户可以从报告详情下载 Markdown 报告。
- 运营用户可以下载证据包，看到报告结论背后的 evidence refs、原始评论预览、来源 URL 和缺失原因。
- 开发者可以通过 API 和测试证明导出内容不泄露敏感 metadata。

功能范围：

- `GET /api/reports/{report_id}/export/markdown`
- `GET /api/reports/{report_id}/evidence-package`
- 前端报告详情页新增 `导出 Markdown` 和 `下载证据包`。
- mock 模式下前端使用 data URL 生成本地下载内容。
- 真实 API 模式下前端指向 FastAPI 导出接口。

非目标：

- 不做 PDF。
- 不重新生成报告，只导出已入库报告。
- 不调用 LLM。
- 不把完整 Agent tool input/output 暴露进证据包。
- 不导出 secret、token、password、authorization、api_key 等敏感 metadata。

验收标准：

- Markdown 导出返回 `text/markdown`。
- Markdown 导出带 `Content-Disposition` 文件名。
- evidence package 返回统一 envelope，并带 JSON 下载文件名。
- evidence package 包含 `report_id`、`task_id`、`evidence_refs`、`sources`、`missing_refs`。
- evidence package 对敏感 metadata 做过滤。
- 前端报告详情页能看到两个中文下载入口。
- Playwright E2E 能看到导出按钮。

## 前置依赖

- `day-16.md`：Markdown 渲染和报告入库。
- `day-17.md`：证据链回查和 citation。
- `day-18.md`：风险评分。
- `day-21.md`：报告详情 API。
- `day-31.md`：中文界面。
- `day-37.md`：Playwright E2E 主链路。
- `../supporting/api-contract.md`：API 契约。
- `../supporting/security-compliance.md`：导出脱敏边界。

## 当天交付物

- Markdown 报告导出接口。
- JSON evidence package 导出接口。
- 导出文件命名规则。
- 证据包 metadata 脱敏。
- 前端报告详情下载入口。
- mock / real API 下载路径边界。
- 导出相关后端、前端和 E2E 回归测试。

## 实施步骤

1. 先写后端导出测试：
   - Markdown 下载响应。
   - evidence package JSON envelope。
   - 缺失报告统一错误 envelope。
   - 敏感 metadata 不进入导出内容。
2. 实现 `backend/app/reporting/export.py`。
3. 在报告路由新增导出接口。
4. 补前端下载 URL helper：
   - mock 模式：data URL。
   - real API 模式：FastAPI endpoint。
5. 在 `ReportViewer` 增加中文下载入口。
6. 更新 E2E，报告详情页必须能看到 `导出 Markdown` 和 `下载证据包`。
7. 回填文档。

## 测试计划

计划执行：

```powershell
uv run pytest tests\test_report_export.py
uv run pytest tests\test_frontend_history_contract.py
uv run pytest tests\test_report_generation.py tests\test_report_evidence_chain.py
uv run ruff check backend tests migrations
cd frontend
npm run lint
npm run build
npm run test:e2e
```

补充说明：

- 后端导出测试验证 API 响应、文件名、证据包字段和脱敏。
- 前端契约测试验证下载 URL helper 和按钮文案。
- Playwright E2E 验证报告详情页能看到导出入口。
- 当前不验证真实浏览器下载后的本地文件内容。

## 验收标准

- `GET /api/reports/{report_id}/export/markdown` 返回已入库报告的 Markdown 内容，不重新调用 LLM。
- Markdown 导出响应包含 `text/markdown; charset=utf-8` 和稳定的 `Content-Disposition` 文件名。
- `GET /api/reports/{report_id}/evidence-package` 返回统一 success envelope，并包含 JSON 下载文件名。
- evidence package 至少包含 `report_id`、`task_id`、`evidence_refs`、`sources`、`missing_refs` 和导出时间。
- evidence package 会过滤 `api_key`、`apikey`、`token`、`secret`、`password`、`authorization` 等敏感 metadata key。
- 前端报告详情页展示中文入口：`导出 Markdown`、`下载证据包`。
- mock 模式和真实 API 模式的下载 URL 边界清楚，mock 不伪装成真实后端下载。
- Playwright E2E 能在主链路里看到报告导出入口，证明用户可见交付物已经接入。

## 实际完成

后端改动：

- 新增 `backend/app/reporting/export.py`。
- 新增 `GET /api/reports/{report_id}/export/markdown`。
- 新增 `GET /api/reports/{report_id}/evidence-package`。
- 复用 `SQLAlchemyEvidenceChainStore` 回查 evidence refs。
- evidence package 过滤敏感 metadata key：`api_key`、`apikey`、`token`、`secret`、`password`、`authorization`。
- evidence package 对疑似 secret value 做 `[REDACTED]`。

前端改动：

- `frontend/src/lib/api.ts` 新增 `getReportMarkdownExportUrl()` 和 `getReportEvidencePackageUrl()`。
- mock 模式生成本地 data URL，真实 API 模式指向 FastAPI endpoint。
- `frontend/src/components/report-viewer.tsx` 新增 `导出 Markdown` 和 `下载证据包`。
- `frontend/e2e/marketmind-main-flow.spec.ts` 增加报告详情下载入口断言。

测试改动：

- 新增 `tests/test_report_export.py`。
- 更新 `tests/test_frontend_history_contract.py`。

## 当前验证结果

RED：

- `uv run pytest tests\test_report_export.py` 最初失败，原因是导出接口不存在。
- `uv run pytest tests\test_frontend_history_contract.py` 最初失败，原因是前端没有导出 URL helper 和下载入口。

GREEN：

```powershell
uv run pytest tests\test_report_export.py tests\test_frontend_history_contract.py tests\test_report_generation.py tests\test_report_evidence_chain.py
# 19 passed

uv run ruff check backend tests migrations
# All checks passed

cd frontend
npm run lint
# passed

npm run build
# passed

npm run test:e2e
# 1 passed
```

验证注意：

- 曾经并行运行 `npm run build` 和 `npm run test:e2e`，Next.js 在 Windows `.next` 写入时出现 `EPERM rename` 日志。之后顺序重跑 `npm run test:e2e`，结果干净通过。

## 遗留问题

- 当前不做 PDF。
- 当前 evidence package 只导出 evidence source 预览，不导出完整 HTML / screenshot 二进制 artifact。
- 当前真实 API 下载入口需要后端服务运行；mock 模式只用于本地演示和 E2E。
- 当前没有对大报告导出做分页或压缩。

## 风险与回退

风险：

- 导出内容和页面展示不一致。
- metadata 泄露内部字段。
- 证据包字段后续扩展导致前端和 API 口径漂移。
- PDF 需求提前进入导致范围膨胀。

回退：

- 先保留 Markdown 和 JSON evidence package。
- 如果证据包字段有争议，优先保留最小字段：`evidence_ref`、`source_type`、`source_url`、`content_preview`、`missing_reason`。
- PDF 作为后续独立功能，不影响 Day38。

## 文档同步清单

- `api-contract.md`：新增两个导出接口。
- `testing-strategy.md`：记录导出测试边界。
- `development-log.md`：记录 Day38 实际开发和验证。
- `interview-defense-dossier.md`：补充报告交付物讲法。
- `security-compliance.md`：记录导出脱敏边界。

## 面试讲法

可以这样讲：

> Day38 我把报告从页面展示推进到可交付 artifact。运营同学可以下载 Markdown 报告和 JSON 证据包，证据包里保留 evidence refs、来源 URL、评论预览和缺失原因。这样报告不是一段不可追溯的模型文本，而是能回到证据链的交付物。

如果被问“为什么不做 PDF”，回答：

> PDF 会引入排版和渲染复杂度。当前更重要的是结构化、可追溯、可测试的内容交付，所以先做 Markdown 和 JSON evidence package。等报告结构稳定后再做 PDF 更合理。

## 建议提交

```text
feat: 增加报告 Markdown 导出和证据包
```
