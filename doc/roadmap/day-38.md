# Day 38 - 报告导出与证据包

## 当天目标

Day 38 的目标是让报告从“页面里能看”升级为“可以交付给别人”。对电商运营场景来说，用户最终需要的是可保存、可分享、可复盘的报告交付物，而不仅是控制台页面。

这一天要实现或规划报告 Markdown 导出、证据包 artifact、证据引用清单和导出按钮，让报告具备更实际的业务价值。

## 前置依赖

- `day-16.md`：Markdown 渲染和报告入库。
- `day-17.md`：证据链回查和 citation。
- `day-18.md`：风险评分。
- `day-21.md`：报告详情 API。
- `day-31.md`：中文界面。
- `../supporting/reporting` 相关文档：报告 schema、证据链、导出边界。
- `../supporting/security-compliance.md`：导出内容脱敏和合规边界。

## 当天交付物

- 新增报告导出能力：
  - Markdown 导出。
  - 可选 JSON evidence package。
  - 导出文件名规则。
- 前端报告详情页增加：
  - `导出 Markdown`。
  - `下载证据包`。
  - 导出失败提示。
- 后端 API 可选：
  - `GET /api/reports/{report_id}/export/markdown`。
  - `GET /api/reports/{report_id}/evidence-package`。
- evidence package 包含：
  - report_id。
  - task_id。
  - evidence_refs。
  - source_url。
  - content_preview。
  - missing_reason。
  - generated_at。
- 文档明确暂不做 PDF，除非后续需要。

## 实施步骤

1. 先写测试：
   - `tests/test_report_export.py`。
   - 验证 Markdown 导出包含标题、评分、section、evidence_refs。
   - 验证 evidence package 不包含敏感字段。
2. 后端导出：
   - 复用现有 Markdown renderer。
   - 不重复生成报告，只读取已入库报告。
   - 404 使用统一 envelope。
3. 前端接入：
   - 报告详情页增加中文按钮。
   - mock 模式下也能下载本地生成内容。
4. 文件命名：
   - `marketmind-report-{report_id}.md`。
   - `marketmind-evidence-{report_id}.json`。
5. 安全检查：
   - source_url 可以保留。
   - 不导出 API key、内部错误 stack。
   - evidence missing reason 可以保留。

## 测试计划

```powershell
uv run pytest tests\test_report_export.py
uv run pytest tests\test_report_generation.py tests\test_report_evidence_chain.py
uv run pytest tests\test_frontend_history_contract.py
cd frontend
npm run lint
npm run build
```

如果增加浏览器下载 E2E，可接 Day37 的 Playwright helper。

## 验收标准

- 报告详情页能看到导出入口。
- Markdown 导出内容包含证据引用。
- evidence package 可以单独下载或通过 API 获取。
- 导出接口不泄露敏感配置。
- mock 和真实 API 路径边界明确。
- 文档说明 PDF 暂不做或延后。

## 风险与回退

风险：

- 导出内容和页面报告不一致。
- evidence package 泄露内部 metadata。
- 文件下载在 Next.js server/client 边界处理复杂。
- PDF 需求扩散导致范围膨胀。

回退：

- 首版只做 Markdown，不做 PDF。
- 如果前端下载复杂，先提供 API endpoint 和复制 Markdown。
- 如果证据包字段不确定，先导出最小 evidence_refs 清单。

## 文档同步清单

- `development-log.md`：记录 Day 38 导出能力和验证结果。
- `interview-defense-dossier.md`：补充“项目实际价值如何落地”的回答。
- `testing-strategy.md`：记录导出测试边界。
- `api-contract.md`：如果新增导出 API，更新契约。
- `security-compliance.md`：记录导出脱敏边界。

## 面试讲法

可以这样讲：

> Day 38 我把报告从页面展示推进到可交付 artifact。运营同学不一定一直待在系统里，他们需要 Markdown 报告和证据包去复盘或发给同事。导出内容保留 evidence_refs，所以报告不是一段不可追溯的模型文本，而是能回到证据链的交付物。

如果被问“为什么不直接做 PDF”，回答：

> PDF 会引入排版和渲染复杂度。当前更重要的是结构化可追溯内容，所以先做 Markdown 和 JSON evidence package。等报告结构稳定后再做 PDF 更合理。

## 建议提交

```text
feat: 增加报告 Markdown 导出和证据包
```
