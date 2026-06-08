# Day 27 主链路 Benchmark

这份结果来自 20 个 fixture 样例任务，目标是稳定复现主链路各阶段耗时。当前不代表真实外部网站、真实 Redis/Celery broker 或真实 LLM API 性能。

## 总览

- 样本数：20
- 成功数：19
- 失败数：1
- 成功率：95.00%
- 平均端到端耗时：338 ms
- P50 端到端耗时：347 ms
- P95 端到端耗时：391 ms
- 模型调用次数：0
- Token 总量：0

## 阶段瓶颈

| 阶段 | 平均耗时 ms | 样本数 | 平均占比 |
| --- | ---: | ---: | ---: |
| crawler | 129 | 20 | 38.17% |
| rag | 84 | 19 | 24.85% |
| report | 64 | 19 | 18.93% |
| agent | 50 | 19 | 14.79% |
| api | 14 | 20 | 4.14% |
| queue | 7 | 20 | 2.07% |

## 失败分类

| 错误码 | 次数 |
| --- | ---: |
| ACCESS_BLOCKED | 1 |

## 样例任务

| task_id | source_id | status | total_duration_ms | error_code |
| --- | --- | --- | ---: | --- |
| bench_tsk_01 | fixture-product-01 | completed | 305 | - |
| bench_tsk_02 | fixture-product-02 | completed | 347 | - |
| bench_tsk_03 | fixture-product-03 | completed | 386 | - |
| bench_tsk_04 | fixture-product-04 | completed | 388 | - |
| bench_tsk_05 | fixture-product-05 | completed | 320 | - |
| bench_tsk_06 | fixture-product-06 | completed | 305 | - |
| bench_tsk_07 | fixture-product-07 | completed | 347 | - |
| bench_tsk_08 | fixture-product-08 | completed | 349 | - |
| bench_tsk_09 | fixture-product-09 | completed | 388 | - |
| bench_tsk_10 | fixture-product-10 | completed | 320 | - |
| bench_tsk_11 | fixture-product-11 | completed | 362 | - |
| bench_tsk_12 | fixture-product-12 | completed | 307 | - |
| bench_tsk_13 | fixture-product-13 | failed | 221 | ACCESS_BLOCKED |
| bench_tsk_14 | fixture-product-14 | completed | 391 | - |
| bench_tsk_15 | fixture-product-15 | completed | 320 | - |
| bench_tsk_16 | fixture-product-16 | completed | 322 | - |
| bench_tsk_17 | fixture-product-17 | completed | 364 | - |
| bench_tsk_18 | fixture-product-18 | completed | 349 | - |
| bench_tsk_19 | fixture-product-19 | completed | 391 | - |
| bench_tsk_20 | fixture-product-20 | completed | 283 | - |
