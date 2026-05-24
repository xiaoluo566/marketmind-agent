# 部署与版本管理

## 部署方式

- 本地开发：Python 虚拟环境
- 集成开发：Docker Compose
- 未来部署：可拆到独立服务或单机容器组

## Docker Compose 服务

第一版建议包含：

- `api`
- `worker`
- `postgres`
- `redis`
- `streamlit`

后续可选：

- `crawler-worker`
- `scheduler`
- `monitor`

## 版本管理

- 每天至少一个可回退提交
- 里程碑打 tag
- 重大架构变更先写文档再改代码

## 回退策略

- 保留数据库迁移脚本
- 保留上一个可用镜像或分支
- 出现高风险变更时先创建 backup branch

## 环境变量

- 数据库连接
- Redis 地址
- 模型提供方配置
- 爬虫站点配置
- Web 前端配置

## 启动顺序

1. 启动数据库和 Redis
2. 执行数据库迁移
3. 启动 API
4. 启动 Celery worker
5. 启动前端控制台
6. 跑健康检查和样例任务

## 回退检查

回退不是只退代码，还要检查：

- 数据库迁移是否兼容
- Worker 是否仍能消费旧任务
- 前端是否能读取旧报告
- `.env.example` 是否发生变化

## 与其他文档关系

- 环境细节见 `dev-environment.md`
- 发布清单见 `release-checklist.md`
- 测试门槛见 `testing-strategy.md`
