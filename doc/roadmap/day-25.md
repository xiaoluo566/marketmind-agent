# Day 25 - Docker Compose 与环境固化

## 当天目标

让项目从“我电脑能跑”变成“别人按文档也能跑”。这是工程化简历项目的重要分水岭。

## 前置依赖

- `day-24.md` 主链路可测试
- 阅读 `../supporting/deployment.md`
- 阅读 `../supporting/dev-environment.md`

## 当天交付物

- `docker-compose.yml`
- `.env.example`
- API service
- Worker service
- PostgreSQL service
- Redis service
- 前端 service

## 实施步骤

1. 写 Postgres 和 Redis 服务
2. 写 API Dockerfile 或服务启动命令
3. 写 Worker 启动命令
4. 配置数据库和 Redis 环境变量
5. 用 compose 跑健康检查和样例任务

## 验收标准

- 新环境能按 README 启动
- API 和 Worker 能连上同一个数据库
- `.env` 不进入 Git
- `.env.example` 包含必要变量

## 风险与回退

- 如果容器化拖慢开发，先保证本地原生启动可用
- 数据库数据卷要明确是否会被清理

## 关联文档

- 上一天：`day-24.md`
- 下一天：`day-26.md`
- 部署：`../supporting/deployment.md`
- 安全：`../supporting/security-compliance.md`

## 建议提交

`feat: add docker compose workflow`

