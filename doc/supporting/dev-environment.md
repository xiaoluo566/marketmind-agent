# 开发环境

## 本机假设

- Windows 为主
- PowerShell 可用
- Git 已安装
- GitHub CLI 已登录
- Python 和 Node 只在需要时启用

## 推荐工具链

- Python 3.11 或 3.12
- `uv` 或 `venv` 管理 Python 环境
- Docker Desktop 负责本地服务
- GitHub CLI 负责仓库创建、推送和版本查看
- Playwright 负责浏览器自动化

## 本地目录约定

- 仓库根目录：项目代码和文档
- `doc/`：规划和规范
- `src/`：后续实现代码
- `tests/`：测试
- `data/`：本地样例数据和临时输出

## 环境变量约定

- `DATABASE_URL`
- `REDIS_URL`
- `MODEL_PROVIDER`
- `MODEL_NAME`
- `APP_ENV`
- `LOG_LEVEL`

## 依赖关系

这个文档与 `deployment.md`、`testing-strategy.md`、`release-checklist.md` 共同决定项目能不能被别人复制起来。

## 开发纪律

- 环境配置先文档化再写代码
- 任何新依赖都要说明用途和可替代方案
- 本机可以跑通后再考虑容器化

