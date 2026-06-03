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

## 作用

这些示例是给 `api-contract.md`、`data-model.md`、`agent-state-machine.md`、`model-and-data-decisions.md` 和 `testing-strategy.md` 共用的参考样例。
