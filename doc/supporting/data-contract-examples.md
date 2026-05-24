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

## 创建任务响应

```json
{
  "success": true,
  "data": {
    "task_id": "tsk_01HXYZ",
    "status": "received"
  },
  "message": "accepted",
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

这些示例是给 `api-contract.md`、`data-model.md`、`agent-state-machine.md` 和 `testing-strategy.md` 共用的参考样例。

