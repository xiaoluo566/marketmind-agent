# Day 04 - FastAPI 项目骨架

## 当天目标

建立后端入口，让项目有可启动、可检查、可扩展的 API 基础。今天只做网关骨架，不在 API 里直接执行长任务。

## 前置依赖

- `day-03.md` 数据模型草案已确定
- 阅读 `../supporting/api-contract.md`
- 阅读 `../supporting/dev-environment.md`

## 当天交付物

- FastAPI app
- 健康检查接口
- 配置读取模块
- 统一响应 envelope
- 错误码基础结构

## 实施步骤

1. 创建后端目录结构，例如 `src/app/api`、`src/app/core`
2. 实现配置加载，优先从环境变量读取
3. 实现 `GET /health`
4. 实现统一响应格式：`success`、`data`、`error`、`trace_id`
5. 准备 Pydantic 请求模型，但暂不接入真实任务

## 验收标准

- 本地能启动 API
- `/health` 返回正常
- 错误响应格式统一
- API 代码没有直接依赖爬虫或模型调用

## 风险与回退

- 不要把业务逻辑写进路由函数
- 如果配置混乱，先回到 `../supporting/dev-environment.md` 明确变量

## 关联文档

- 上一天：`day-03.md`
- 下一天：`day-05.md`
- API 契约：`../supporting/api-contract.md`
- 安全：`../supporting/security-compliance.md`

## 建议提交

`feat: scaffold fastapi gateway`

