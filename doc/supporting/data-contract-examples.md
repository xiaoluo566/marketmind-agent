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

## Agent step 记录示例

```json
{
  "task_id": "tsk_01HXYZ",
  "step_type": "action",
  "tool_name": "crawl_product_tool",
  "status": "pending",
  "input": {
    "url": "https://example.com/product/123"
  }
}
```

## 作用

这些示例是给 `api-contract.md`、`data-model.md`、`agent-state-machine.md`、`model-and-data-decisions.md` 和 `testing-strategy.md` 共用的参考样例。
