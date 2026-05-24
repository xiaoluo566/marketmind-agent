# 系统架构

## 结构原则

第一版采用“模块化单体 + 异步任务分层”的方式，而不是一上来就拆成复杂微服务。逻辑上分层，部署上先收敛，等瓶颈明确后再拆。

## 逻辑分层

1. 前端控制台
2. FastAPI 业务网关
3. Celery 异步任务层
4. Agent 决策层
5. Playwright 采集层
6. PostgreSQL / Redis 持久化层

## 目标拓扑

第一版可以用一个后端代码仓库承载多个逻辑模块：

- `api`：FastAPI 路由、请求校验、响应封装
- `tasks`：Celery app、任务定义、重试策略
- `agent`：Agent loop、工具注册、状态恢复
- `crawler`：Playwright 采集器、页面适配器、抽取器
- `rag`：清洗、切片、embedding、pgvector 检索
- `reports`：报告结构、报告生成、证据引用
- `storage`：SQLAlchemy 模型、repository、迁移
- `observability`：日志、trace、指标

部署时可以先是一组 Docker Compose 服务：`api`、`worker`、`postgres`、`redis`。代码上保持清晰边界，后续如果 worker 压力变大，再把 `crawler-worker` 或 `rag-worker` 拆出去。

## 核心边界

- API 层只负责接收请求、鉴权、校验、派发任务
- Celery 层只负责异步执行和重试
- Agent 层只负责决策、工具调用和状态流转
- 爬虫层只负责采集和抽取，不承担业务判断
- 数据层只负责存储和检索，不写业务规则

## 为什么这样拆

- 可以把长任务从 HTTP 请求中解耦
- 可以独立替换前端
- 可以独立替换爬虫或模型提供方
- 可以清楚定位故障层

## 主请求生命周期

1. 用户在前端提交链接或上传数据
2. FastAPI 校验请求，创建 `tasks` 记录
3. API 把任务投递给 Celery，并立即返回 `task_id`
4. Worker 加载任务上下文，启动 Agent run
5. Agent 选择工具并写入 `agent_steps`
6. 工具执行爬虫、清洗、检索或报告生成
7. 每一步结果写入数据库，同时写入 `task_events`
8. 前端通过轮询、SSE 或 WebSocket 读取进度
9. 报告生成后，任务状态变为 `completed`

## 失败隔离

| 故障层 | 典型症状 | 系统应如何处理 |
| --- | --- | --- |
| API | 参数错误、URL 不合法 | 返回 4xx，任务不入队 |
| Celery | Worker 未启动、队列堵塞 | 任务保持 queued，前端显示等待 |
| Crawler | 页面加载失败、DOM 变化 | 写入失败事件，允许重试或导入兜底 |
| Agent | 输出格式错、工具选择错 | Pydantic 拦截，触发 self-heal |
| RAG | embedding 失败、召回为空 | 记录降级原因，报告中标注证据不足 |
| Database | 写入失败、迁移缺失 | 任务失败并记录 trace_id |

## 后续可扩展点

- WebSocket / SSE 进度推送
- 独立 worker 池
- 独立 report service
- 任务队列分级

## 与其他文档关系

- 表结构和状态字段见 `data-model.md`
- API 输入输出见 `api-contract.md`
- Agent 状态流见 `agent-state-machine.md`
- 部署细节见 `deployment.md`
