# 技术选型说明

## 采用的栈

- 后端：FastAPI
- ORM：SQLAlchemy + Alembic
- 数据库：PostgreSQL
- 缓存 / 队列：Redis
- 异步任务：Celery
- 爬虫：Playwright Async
- 结构化校验：Pydantic
- 重试：Tenacity
- 向量检索：pgvector
- 前端：Stitch 生成 UI，后端负责 API 和接入
- 容器化：Docker Compose
- 测试：pytest

## 选型理由

- FastAPI 适合做 API 网关和文档输出
- PostgreSQL 同时能承载业务数据和长期状态
- Redis 适合任务状态、短期缓存和消息中转
- Celery 适合长任务解耦
- Playwright 比纯 requests 更适合真实网页
- pgvector 能让项目在一个数据库里完成向量检索闭环

## 替代方案比较

| 位置 | 当前选择 | 替代方案 | 当前不选的原因 |
| --- | --- | --- | --- |
| API | FastAPI | Django、Flask | FastAPI 更轻，Pydantic 集成更自然 |
| 异步任务 | Celery | RQ、Dramatiq、Temporal | Celery 生态成熟，简历辨识度高 |
| 队列缓存 | Redis | RabbitMQ | Redis 同时能做缓存和队列 broker |
| 数据库 | PostgreSQL | MySQL、SQLite | pgvector 和复杂查询更适合 PostgreSQL |
| 向量库 | pgvector | Milvus、Qdrant | 第一版少一个外部系统，部署更稳 |
| 前端 | Stitch 生成 UI | Streamlit、Next.js 手写 | 让主要开发时间集中在后端工程、Agent 状态机和 RAG |
| 爬虫 | Playwright | Selenium、requests | Playwright 对动态页面更稳定 |

## 暂不优先的技术

- Kafka：第一版太重
- Milvus：除非数据规模上来
- Kubernetes：除非部署复杂度明显增长
- 复杂微服务拆分：第一版不需要

## 选型原则

- 能跑通闭环优先
- 能解释清楚优于堆名词
- 能维护优于能炫技

## 什么时候重新评估

- 如果任务吞吐超过单机 Celery 能力，再考虑队列拆分
- 如果评论规模超过 pgvector 查询舒适区，再考虑 Milvus 或 Qdrant
- 如果 Stitch 生成代码难以维护，再评估改为手写 Next.js 或简化控制台
- 如果 prompt 版本太多，再引入专门的 prompt registry
