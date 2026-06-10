# 安全与合规边界

## 输入安全

- 所有 API 输入先过 Pydantic
- URL 必须校验协议和域名
- 不允许任意文件路径读取
- 上传文件限制大小和类型

### 当前实现状态

- `TaskCreateRequest` 已通过 Pydantic 校验 `source_type=public_url` 的 target。
- `public_url` 只允许 `http` 和 `https`。
- `public_url` 拒绝 localhost、`.local`、loopback、private、link-local、reserved、multicast、unspecified 地址。
- 回归测试：`tests/test_tasks_api.py::test_create_task_rejects_unsafe_public_url_targets`。

## Secret 管理

- API key 不进 Git
- `.env` 不提交
- 使用 `.env.example` 声明变量
- 日志中不打印密钥

### Day34 embedding provider 安全补充

Day34 把真实 embedding provider 接入层做成了显式配置，但安全边界不变：

- `EMBEDDING_API_KEY` 只能通过环境变量注入，不能写进代码、测试、README 示例值或 Docker Compose 默认值。
- 默认 `EMBEDDING_PROVIDER=fake`，避免本地测试误触真实 API。
- 显式切换到 `openai-compatible` 但缺少 API key 时必须 fail-fast，不允许静默 fallback 到 fake provider。
- `EMBEDDING_PROVIDER_FALLBACK_ENABLED` 默认关闭，避免生产环境把真实配置错误掩盖掉。
- 真实 provider 返回的错误码和响应体只记录必要摘要，不打印完整 header 或 secret。
- provider 调用不应把评论正文当作指令，也不能把外部文本当成可信配置。

## 爬虫合规

- 只采集公开可访问内容
- 不绕过登录和付费墙
- 不攻击验证码
- 限制请求频率
- 保留来源链接

## 数据安全

- 原始数据和报告要关联来源
- 用户输入和模型输出要区分存储
- 出错日志不泄露密钥或个人敏感信息

## 面试表达

可以强调“工程边界”和“失败处理”，不要把项目描述成绕过风控的爬虫。

## 威胁模型

| 风险 | 场景 | 防护 |
| --- | --- | --- |
| SSRF | 用户提交内网 URL | URL 白名单、协议限制 |
| Secret 泄露 | 日志打印 API key | 日志脱敏 |
| 文件滥用 | 上传超大文件 | 类型和大小限制 |
| Prompt 注入 | 评论里包含诱导指令 | 把评论当数据，不当指令 |
| XSS | 报告中渲染 HTML | 前端转义和 Markdown 白名单 |

## Agent 特有安全边界

- 工具调用必须由代码校验参数
- 模型不能直接执行 shell 命令
- 模型不能直接写数据库
- 模型输出必须经过 schema
- 面向前端的 Agent step / evidence chain 只展示摘要和 key 列表，不暴露完整 tool input/output

## 与其他文档关系

- API 输入见 `api-contract.md`
- prompt 边界见 `prompt-strategy.md`
- 上传数据见 `ui-console-spec.md`
