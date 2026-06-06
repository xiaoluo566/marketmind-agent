# 数据契约示例

## 创建任务请求

```json
{
  "target": "https://example.com/product/123",
  "mode": "competitive_research",
  "priority": "normal",
  "options": {
    "use_rag": true,
    "export_format": "markdown"
  }
}
```

## CSV / JSON 导入行示例

CSV 表头或 JSON 对象字段第一版按下面约定：

```json
{
  "product_title": "Portable Espresso Maker",
  "review_content": "The pump stopped working after three days and customer service never replied.",
  "rating": 1,
  "source_url": "https://example.com/product/123",
  "product_id": "EXT-123",
  "review_id": "REV-001",
  "author_hash": "usr_anon_9a21",
  "published_at": "2026-05-01T10:30:00Z",
  "price": 39.99,
  "currency": "USD"
}
```

最小必填字段只有：

- `product_title`
- `review_content`

其他字段缺失时由系统补默认值或写入 `raw_payload`。不要导入真实姓名、手机号、邮箱等隐私字段。

## 创建任务响应

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "status": "queued",
    "trace_id": "trc_01HABC",
    "queue_task_id": "celery_01HQUEUE"
  },
  "message": "accepted",
  "trace_id": "trc_01HABC"
}
```

## 查询任务状态响应

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "status": "queued",
    "trace_id": "trc_01HABC",
    "target": "https://example.com/product/123",
    "mode": "competitive_research",
    "priority": "normal",
    "source_type": "public_url",
    "options": {
      "use_rag": true,
      "export_format": "markdown"
    },
    "queue_task_id": "celery_01HQUEUE",
    "started_at": null,
    "finished_at": null,
    "error_code": null,
    "error_message": null,
    "created_at": "2026-05-25T10:00:00Z",
    "updated_at": "2026-05-25T10:00:01Z"
  },
  "message": "ok",
  "trace_id": "trc_01HABC"
}
```

## 查询任务事件响应

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "events": [
      {
        "event_id": "evt_01H001",
        "task_id": "tsk_01HXYZ",
        "status": "received",
        "event_type": "status",
        "message": "task received",
        "payload": {
          "target": "https://example.com/product/123",
          "mode": "competitive_research",
          "priority": "normal",
          "source_type": "public_url"
        },
        "trace_id": "trc_01HABC",
        "created_at": "2026-05-25T10:00:00Z"
      },
      {
        "event_id": "evt_01H002",
        "task_id": "tsk_01HXYZ",
        "status": "queued",
        "event_type": "status",
        "message": "task queued",
        "payload": {
          "queue_task_id": "celery_01HQUEUE"
        },
        "trace_id": "trc_01HABC",
        "created_at": "2026-05-25T10:00:01Z"
      }
    ]
  },
  "message": "ok",
  "trace_id": "trc_01HABC"
}
```

## 采集成功事件示例

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "events": [
      {
        "event_id": "evt_01H003",
        "task_id": "tsk_01HXYZ",
        "status": "running",
        "event_type": "crawler",
        "message": "crawl started",
        "payload": {
          "target": "https://example.com/product/123"
        },
        "trace_id": "trc_01HABC",
        "created_at": "2026-05-25T10:00:02Z"
      },
      {
        "event_id": "evt_01H004",
        "task_id": "tsk_01HXYZ",
        "status": "running",
        "event_type": "crawler",
        "message": "crawl completed",
        "payload": {
          "url": "https://example.com/product/123",
          "title": "Portable Espresso Maker",
          "price": 39.99,
          "rating": 4.6,
          "source_type": "html_fixture",
          "text_preview": "Portable Espresso Maker Travel ready. Only $39.99 today.",
          "reviews": [
            {
              "external_id": "rev-001",
              "content": "The pump stopped working after three days.",
              "rating": 1.0,
              "source_url": "https://example.com/product/123#rev-001",
              "metadata": {
                "extractor": "generic_html_review"
              }
            }
          ],
          "artifacts": [
            {
              "artifact_type": "crawler_html",
              "path": "data/artifacts/crawler/tsk_01HXYZ/20260525T100003000000Z_crawler_html.html",
              "mime_type": "text/html",
              "checksum": "sha256_hex",
              "metadata": {
                "task_id": "tsk_01HXYZ"
              }
            }
          ],
          "persisted": {
            "product_id": "prd_01HPRODUCT",
            "page_id": "pg_01HPAGE",
            "artifact_ids": ["art_01HHTML"],
            "review_ids": ["rev_01HREVIEW"]
          }
        },
        "trace_id": "trc_01HABC",
        "created_at": "2026-05-25T10:00:03Z"
      }
    ]
  },
  "message": "ok",
  "trace_id": "trc_01HABC"
}
```

## 采集失败事件示例

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "events": [
      {
        "event_id": "evt_01H005",
        "task_id": "tsk_01HXYZ",
        "status": "failed",
        "event_type": "crawler_error",
        "message": "crawl failed",
        "payload": {
          "error_code": "ACCESS_BLOCKED",
          "reason": "page appears to be blocked by access controls",
          "details": {
            "url": "https://example.com/product/blocked",
            "artifacts": [
              {
                "artifact_type": "crawler_failure_html",
                "path": "data/artifacts/crawler/tsk_01HXYZ/20260525T100003000000Z_crawler_failure_html.html",
                "mime_type": "text/html",
                "checksum": "sha256_hex",
                "metadata": {
                  "task_id": "tsk_01HXYZ"
                }
              }
            ]
          }
        },
        "trace_id": "trc_01HABC",
        "created_at": "2026-05-25T10:00:03Z"
      }
    ]
  },
  "message": "ok",
  "trace_id": "trc_01HABC"
}
```

## Agent step 记录示例

```json
{
  "agent_run_id": "run_01HXYZ",
  "task_id": "tsk_01HXYZ",
  "step_index": 2,
  "step_type": "action",
  "tool_name": "crawl_product_tool",
  "status": "pending",
  "thought": null,
  "tool_input": {
    "url": "https://example.com/product/123",
    "source_type": "html_fixture"
  },
  "tool_output": {},
  "observation": null,
  "error_message": null,
  "started_at": null,
  "finished_at": null
}
```

## Agent run 记录示例

```json
{
  "run_id": "run_01HXYZ",
  "task_id": "tsk_01HXYZ",
  "status": "running",
  "model_provider": "openai-compatible",
  "model_name": "gpt-5.4-mini",
  "report_model_name": "gpt-5.5",
  "prompt_version": "v1",
  "started_at": "2026-05-25T10:00:02Z",
  "finished_at": null
}
```

## Agent Thought / Observation 示例

```json
{
  "agent_run_id": "run_01HXYZ",
  "task_id": "tsk_01HXYZ",
  "step_index": 3,
  "step_type": "observation",
  "status": "success",
  "thought": null,
  "tool_name": "crawl_product_tool",
  "tool_input": {},
  "tool_output": {
    "success": true,
    "data": {
      "title": "Portable Espresso Maker"
    }
  },
  "observation": "采集完成：Portable Espresso Maker，共提取 1 条评论证据。",
  "error_message": null
}
```

## Agent 工具清单示例

```json
{
  "name": "crawl_product_tool",
  "version": "v1",
  "description": "Fetch a public product page or fixture HTML and extract product evidence.",
  "input_schema": "CrawlProductToolInput",
  "output_schema": "CrawlProductToolOutput",
  "idempotent": true,
  "retryable": true,
  "timeout_ms": 60000,
  "error_codes": [
    "PAGE_TIMEOUT",
    "DOM_NOT_FOUND",
    "ACCESS_BLOCKED",
    "NETWORK_ERROR",
    "PARSER_ERROR",
    "UNKNOWN_SITE"
  ]
}
```

## Agent 工具执行结果示例

```json
{
  "tool_name": "crawl_product_tool",
  "tool_version": "v1",
  "success": true,
  "data": {
    "url": "https://example.com/product/123",
    "source_type": "html_fixture",
    "title": "Portable Espresso Maker",
    "price": 39.99,
    "rating": 4.6,
    "extracted_text_preview": "Portable Espresso Maker Travel ready.",
    "reviews": [],
    "artifacts": [],
    "metadata": {
      "extractor": "generic_html",
      "fetched_at": "2026-05-25T10:00:03Z"
    }
  },
  "error": null,
  "artifacts": [],
  "task_id": "tsk_01HXYZ",
  "trace_id": "trc_01HABC",
  "idempotent": true,
  "retryable": true,
  "started_at": "2026-05-25T10:00:02Z",
  "finished_at": "2026-05-25T10:00:03Z",
  "duration_ms": 120
}
```

## 结构化输出修复提示词示例

```text
Prompt name: planner.tool_decision
Schema: AgentToolDecision
Error: Expecting value: line 1 column 1 (char 0)
Please return only valid JSON that matches the schema.
Raw output:
tool_name=crawl_product_tool url=https://example.com/product/espresso
```

## 结构化输出解析结果示例

```json
{
  "prompt_name": "planner.tool_decision",
  "raw_output": "tool_name=crawl_product_tool url=https://example.com/product/espresso",
  "repaired_output": "{\n  \"thought\": \"需要先采集商品页。\",\n  \"action\": \"call_tool\",\n  \"tool_name\": \"crawl_product_tool\",\n  \"tool_input\": {\n    \"url\": \"https://example.com/product/espresso\"\n  }\n}",
  "validation_error_count": 1,
  "self_heal_count": 1,
  "self_healed": true
}
```

## 短期记忆 snapshot 示例

```json
{
  "task_id": "tsk_01HXYZ",
  "summary": "step 1 thought: 需要先采集商品页。 evidence=rev_001\nstep 2 action: 调用工具 crawl_product_tool，参数：{...} evidence=art_01HHTML",
  "summary_evidence_refs": ["rev_001", "art_01HHTML"],
  "recent_entries": [
    {
      "sequence": 3,
      "step_type": "observation",
      "content": "采集完成：Portable Espresso Maker，共提取 4 条评论证据。",
      "evidence_refs": ["rev_002", "rev_003"],
      "metadata": {
        "agent_run_id": "run_01HXYZ",
        "step_id": "stp_01H003",
        "status": "success",
        "tool_name": "crawl_product_tool"
      }
    }
  ],
  "updated_at": "2026-05-25T10:00:05Z"
}
```

## 短期记忆 prompt context 示例

```text
历史摘要：
step 1 thought: 需要先采集商品页。
step 2 action: 调用工具 crawl_product_tool，参数：{...}

最近上下文：
- step 3 observation: 采集完成：Portable Espresso Maker，共提取 4 条评论证据。

证据引用：rev_001, art_01HHTML, rev_002, rev_003
```

## Review chunk 记录示例

```json
{
  "id": "chk_01HXYZ",
  "review_id": "rev_01HREVIEW",
  "task_id": "tsk_01HXYZ",
  "chunk_index": 0,
  "content": "The pump failed after three days. Return request and support were ignored.",
  "embedding": [0.0123, -0.0456],
  "embedding_model": "text-embedding-3-small",
  "embedding_dimensions": 1536,
  "metadata": {
    "review_external_id": "rev-return",
    "source_url": "https://example.com/product/espresso#rev-return",
    "rating": 1.0,
    "source_type": "crawler"
  }
}
```

说明：示例中的 `embedding` 只展示前两位，真实库中是 1536 维向量。

## 相似评论检索结果示例

```json
{
  "chunk_id": "chk_01HXYZ",
  "review_id": "rev_01HREVIEW",
  "review_external_id": "rev-return",
  "content": "The pump failed after three days. Return request and support were ignored.",
  "similarity": 0.82,
  "source_url": "https://example.com/product/espresso#rev-return",
  "rating": 1.0,
  "metadata": {
    "review_external_id": "rev-return",
    "source_url": "https://example.com/product/espresso#rev-return",
    "rating": 1.0,
    "source_type": "crawler"
  }
}
```

## `search_reviews_tool` 输入示例

```json
{
  "task_id": "tsk_01HXYZ",
  "query": "return support",
  "top_k": 5,
  "min_similarity": 0.2,
  "filters": {
    "rating_lte": 2.0,
    "rating_gte": null,
    "source_type": "crawler"
  }
}
```

## `search_reviews_tool` 输出示例

```json
{
  "query": "return support",
  "task_id": "tsk_01HXYZ",
  "results": [
    {
      "chunk_id": "chk_01HXYZ",
      "review_id": "rev_01HREVIEW",
      "review_external_id": "rev-return",
      "content": "The pump failed after three days. Return request and support were ignored.",
      "similarity": 0.82,
      "source_url": "https://example.com/product/espresso#rev-return",
      "rating": 1.0,
      "evidence_ref": "chunk:chk_01HXYZ",
      "metadata": {
        "source_type": "crawler"
      }
    }
  ],
  "evidence_refs": ["chunk:chk_01HXYZ"],
  "no_results_reason": null,
  "metadata": {
    "top_k": 5,
    "min_similarity": 0.2,
    "embedding_model": "fake-embedding-v1",
    "embedding_dimensions": 1536
  }
}
```

召回为空时：

```json
{
  "query": "return support",
  "task_id": "tsk_01HXYZ",
  "results": [],
  "evidence_refs": [],
  "no_results_reason": "NO_REVIEW_CHUNKS_ABOVE_THRESHOLD",
  "metadata": {
    "top_k": 5,
    "min_similarity": 1.0
  }
}
```

## 结构化报告输入示例

Day 16 起，报告生成模块不直接消费自然语言长上下文，而是消费已经结构化的 observations 和 evidence snippets。

```json
{
  "task_id": "tsk_01HXYZ",
  "product_name": "Portable Espresso Maker",
  "observations": [
    "Crawler extracted 3 low-rating reviews.",
    "search_reviews_tool returned evidence for return support and logistics."
  ],
  "requested_focus": ["return support", "logistics"],
  "evidence_snippets": [
    {
      "evidence_ref": "chunk:chk_return",
      "content": "The pump failed after three days and support ignored the return request.",
      "similarity": 0.86,
      "rating": 1.0,
      "source_url": "https://example.com/product/espresso#rev-return",
      "metadata": {
        "query": "return support"
      }
    }
  ]
}
```

## 结构化报告 JSON 示例

```json
{
  "task_id": "tsk_01HXYZ",
  "title": "Portable Espresso Maker 证据链分析报告",
  "summary": "基于 1 条可引用评论证据，Portable Espresso Maker 当前需要重点关注：return support。",
  "status": "draft",
  "schema_version": "report.v1",
  "evidence_refs": ["chunk:chk_return"],
  "sections": [
    {
      "section_id": "customer_pain_points",
      "heading": "用户痛点",
      "claim": "最高相关证据显示用户痛点集中在：The pump failed after three days and support ignored the return request.",
      "evidence_refs": ["chunk:chk_return"],
      "severity": "high",
      "recommendation": "优先把该痛点拆成可验证的产品改进假设。",
      "metadata": {}
    }
  ],
  "metadata": {
    "requested_focus": ["return support"],
    "generator": "deterministic.report.v1"
  }
}
```

核心约束：

- `sections[*].evidence_refs` 必须是顶层 `evidence_refs` 的子集。
- `evidence_refs` 为空时，`status` 必须表达证据不足，不能输出确定性风险结论。
- `schema_version` 当前为 `report.v1`。

## 结构化报告 Markdown 示例

```markdown
# Portable Espresso Maker 证据链分析报告

- 状态：`draft`
- Schema：`report.v1`

## 摘要

基于 1 条可引用评论证据，Portable Espresso Maker 当前需要重点关注：return support。

## 用户痛点

最高相关证据显示用户痛点集中在：The pump failed after three days and support ignored the return request.

- 风险等级：`high`
- 证据引用：`chunk:chk_return`
- 建议动作：优先把该痛点拆成可验证的产品改进假设。

## 证据摘录

### chunk:chk_return

The pump failed after three days and support ignored the return request.
```

## Evidence chain 示例

Day 17 起，报告详情可以通过 evidence chain 回查来源。`evidence_ref` 不只是一段 Markdown 文本，而是可被后端解析的引用协议。

```json
{
  "task_id": "tsk_01HXYZ",
  "evidence_refs": ["chunk:chk_return", "artifact:art_html", "step:stp_search"],
  "missing_refs": [],
  "sources": [
    {
      "evidence_ref": "chunk:chk_return",
      "source_type": "review_chunk",
      "source_id": "chk_return",
      "task_id": "tsk_01HXYZ",
      "available": true,
      "title": "Review chunk #0",
      "content_preview": "The pump failed after three days and support ignored the return request.",
      "source_url": "https://example.com/product/espresso#return-001",
      "parent_refs": ["review:rev_return"],
      "missing_reason": null,
      "metadata": {
        "chunk_index": 0,
        "rating": 1.0,
        "source_type": "crawler",
        "embedding_model": "fake-embedding-v1",
        "embedding_dimensions": 1536
      }
    },
    {
      "evidence_ref": "artifact:art_html",
      "source_type": "artifact",
      "source_id": "art_html",
      "task_id": "tsk_01HXYZ",
      "available": true,
      "title": "crawler_html",
      "content_preview": "data/artifacts/crawler/tsk_01HXYZ/page.html",
      "source_url": "https://example.com/product/espresso",
      "parent_refs": [],
      "missing_reason": null,
      "metadata": {
        "artifact_type": "crawler_html",
        "mime_type": "text/html",
        "checksum": "checksum-html"
      }
    }
  ]
}
```

缺失证据示例：

```json
{
  "evidence_refs": ["chunk:missing"],
  "missing_refs": ["chunk:missing"],
  "sources": [
    {
      "evidence_ref": "chunk:missing",
      "source_type": "missing",
      "source_id": "missing",
      "available": false,
      "missing_reason": "EVIDENCE_NOT_FOUND"
    }
  ]
}
```

## `GET /api/reports/{report_id}/evidence` 输出示例

```json
{
  "success": true,
  "data": {
    "report_id": "rpt_01HXYZ",
    "task_id": "tsk_01HXYZ",
    "evidence_refs": ["chunk:chk_return"],
    "missing_refs": [],
    "sources": [
      {
        "evidence_ref": "chunk:chk_return",
        "source_type": "review_chunk",
        "source_id": "chk_return",
        "task_id": "tsk_01HXYZ",
        "available": true,
        "title": "Review chunk #0",
        "content_preview": "The pump failed after three days and support ignored the return request.",
        "source_url": "https://example.com/product/espresso#return-001",
        "parent_refs": ["review:rev_return"],
        "missing_reason": null,
        "metadata": {
          "rating": 1.0,
          "source_type": "crawler"
        }
      }
    ]
  },
  "error": null,
  "message": "ok",
  "trace_id": "trc_01HXYZ"
}
```

## Analysis scorecard 示例

Day 18 起，报告可以携带 `analysis_scorecard`，用于展示评论维度风险和机会评分。评分是规则 baseline，不代表销量预测或商业成功概率。

```json
{
  "task_id": "tsk_01HXYZ",
  "status": "scored",
  "overall_risk_score": 82,
  "overall_opportunity_score": 73,
  "evidence_refs": [
    "chunk:chk_quality_1",
    "chunk:chk_quality_2",
    "chunk:chk_support_1"
  ],
  "schema_version": "scorecard.v1",
  "summary": "最高风险维度是 质量风险，风险分 92，基于 2 条证据。评分用于排序和解释，不代表严格商业预测。",
  "dimensions": [
    {
      "dimension": "quality",
      "label": "质量风险",
      "risk_score": 92,
      "opportunity_score": 89,
      "evidence_refs": ["chunk:chk_quality_1", "chunk:chk_quality_2"],
      "sample_size": 2,
      "average_rating": 1.5,
      "max_similarity": 0.91,
      "confidence": 1.0,
      "sample_warning": null,
      "explanation": "质量风险(quality) 基于 2 条证据，平均评分 1.5，风险分 92。",
      "metadata": {
        "minimum_samples": 2
      }
    },
    {
      "dimension": "support",
      "label": "售后风险",
      "risk_score": 50,
      "opportunity_score": 48,
      "evidence_refs": ["chunk:chk_support_1"],
      "sample_size": 1,
      "average_rating": 1.0,
      "max_similarity": 0.86,
      "confidence": 0.5,
      "sample_warning": "LOW_SAMPLE_SIZE",
      "explanation": "售后风险(support) 基于 1 条证据，平均评分 1.0，风险分 50。 样本不足：当前 1 条，低于阈值 2 条，已降权。"
    }
  ]
}
```

嵌入报告时，scorecard 写入：

```json
{
  "metadata": {
    "analysis_scorecard": {
      "schema_version": "scorecard.v1"
    }
  }
}
```

Markdown 会增加：

```markdown
## 维度评分

最高风险维度是 质量风险，风险分 92，基于 2 条证据。评分用于排序和解释，不代表严格商业预测。

- 综合风险分：`82`
- 综合机会分：`73`

### 质量风险

- 风险分：`92`
- 机会分：`89`
- 证据引用：`chunk:chk_quality_1`, `chunk:chk_quality_2`
```

## 作用

这些示例是给 `api-contract.md`、`data-model.md`、`agent-state-machine.md`、`model-and-data-decisions.md` 和 `testing-strategy.md` 共用的参考样例。
