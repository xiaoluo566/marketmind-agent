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
- 前端：Streamlit 优先，后期可切 Next.js
- 容器化：Docker Compose
- 测试：pytest

## 选型理由

- FastAPI 适合做 API 网关和文档输出
- PostgreSQL 同时能承载业务数据和长期状态
- Redis 适合任务状态、短期缓存和消息中转
- Celery 适合长任务解耦
- Playwright 比纯 requests 更适合真实网页
- pgvector 能让项目在一个数据库里完成向量检索闭环

## 暂不优先的技术

- Kafka：第一版太重
- Milvus：除非数据规模上来
- Kubernetes：除非部署复杂度明显增长
- 复杂微服务拆分：第一版不需要

## 选型原则

- 能跑通闭环优先
- 能解释清楚优于堆名词
- 能维护优于能炫技

