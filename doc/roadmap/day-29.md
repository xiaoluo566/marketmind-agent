# Day 29 - README、演示脚本与简历材料整理

## 当天目标

Day 29 的目标不是继续堆业务功能，而是把 Day 1-28 已经完成的工程能力整理成一个别人能读懂、能启动、能听你讲清楚的作品。

今天要解决的问题：

- README 不能只列目录，必须能让陌生人理解项目定位、架构、启动方式和边界。
- 演示不能依赖临场口头解释，必须有固定脚本、备用路线和不能夸大的内容清单。
- 简历 bullet 不能写没有验证的数据，必须基于测试、benchmark 和 CI 结果。
- 面试讲述不能只背技术名词，必须能讲清“为什么不是套壳”“为什么这样做取舍”。

## 前置依赖

- `day-28.md`：失败任务 retry 后端能力已完成。
- `../supporting/demo-script.md`：旧版演示脚本需要重写。
- `../supporting/resume-story.md`：旧版简历表达需要补 Day27/Day28 已验证指标。
- `../supporting/interview-story.md`：旧版讲述稿需要补“不是套壳”和 Day29 文档交付逻辑。
- `../supporting/interview-defense-dossier.md`：作为深度追问来源。
- `../supporting/testing-strategy.md`：记录 Day29 文档契约测试。

## 当天交付物

- 重写 `README.md`。
- 重写 `doc/supporting/demo-script.md`。
- 重写 `doc/supporting/resume-story.md`。
- 重写 `doc/supporting/interview-story.md`。
- 新增 `tests/test_day29_demo_docs.py`。
- 更新 `doc/supporting/testing-strategy.md`。
- 更新 `doc/supporting/development-log.md`。
- 修正历史文档中容易误导的 retry 状态描述。

## 实施步骤

### 1. 写 RED 文档契约测试

先新增 `tests/test_day29_demo_docs.py`，要求：

- README 必须包含 Day 29、快速启动、架构图、演示路径、已知边界和核心演示材料链接。
- demo script 必须包含 5-8 分钟、演示前检查、主线流程、失败重试、备用路线和不要现场声称。
- resume story 必须包含 Day27 fixture benchmark、Day28 失败任务 retry、90.79%、157 passed 和不建议写。
- interview story 必须包含 2 分钟版本、不是套壳、Day 28、Day 29 和追问回答。
- development log 和 testing strategy 必须记录 Day29。

### 2. 重写 README

README 需要成为仓库入口，而不是开发过程备忘录。

必须包含：

- 项目定位。
- Mermaid 架构图。
- 当前能力和未完成能力。
- 快速启动。
- 常用验证命令。
- 演示路径。
- 简历与面试材料入口。
- 已知边界。
- 阅读顺序。
- 分支策略。

### 3. 重写演示脚本

`demo-script.md` 必须明确：

- 5-8 分钟演示结构。
- 演示前检查。
- 主线演示流程。
- 失败重试如何讲。
- benchmark 如何讲。
- 前端、后端、真实网站、Docker 不可用时的备用路线。
- 不能现场声称的内容。

### 4. 重写简历表达

`resume-story.md` 必须只使用已验证事实：

- `157 passed`。
- coverage `90.79%`。
- Day27 fixture benchmark 20 个样例任务、95.00% 成功率、338 ms 平均耗时、391 ms P95。
- Day28 retry tests 7 passed。

不能写：

- 全网稳定采集。
- 真实 LLM 成本统计。
- 完整线上压测。
- 精确 Agent step replay。
- 替代成熟卖家工具。

### 5. 重写面试讲述稿

`interview-story.md` 需要提供：

- 30 秒版本。
- 2 分钟版本。
- 为什么不是套壳。
- 技术选择解释。
- Day28 retry 怎么讲。
- Day29 文档整理怎么讲。
- 高频追问。

### 6. 更新开发日志与测试策略

`development-log.md` 记录真实开发过程。

`testing-strategy.md` 记录 Day29 文档测试边界。

历史文档中“retry 尚未实现”的旧表述要补充说明：当时尚未实现，Day28 已完成后端 retry，剩余是前端入口、Celery countdown 和 Agent step replay。

## 验收标准

- `uv run pytest tests\test_day29_demo_docs.py` 通过。
- README 能让陌生人理解项目定位、架构、启动和边界。
- 演示脚本能支撑 5-8 分钟项目展示。
- 简历表达不包含未验证指标。
- 面试讲述稿能回答“不是套壳”“为什么这样选技术”“当前边界是什么”。
- Day29 文档和开发日志互相引用。

## 风险与回退

- 不要把 README 写成营销页。
- 不要把 fixture benchmark 写成真实生产压测。
- 不要声称 Docker Compose 已真实启动验证。
- 不要把 Day28 retry 说成完整 Agent step replay。
- 如果文档重写后太长，优先保留 README 的启动和边界，详细解释放到 supporting 文档。

## 验证命令

```powershell
uv run pytest tests\test_day29_demo_docs.py
uv run pytest tests\test_day29_demo_docs.py tests\test_day28_recovery.py tests\test_day27_benchmarking.py
uv run pytest
uv run pytest --cov=backend --cov-report=term-missing
uv run ruff check backend tests migrations
uv run alembic heads
docker compose config
cd frontend
npm run lint
npm run build
npm audit --audit-level=high
cd ..
uvx pip-audit
```

当前结果：

```text
uv run pytest tests\test_day29_demo_docs.py: 5 passed
Day27-Day29 targeted tests: 17 passed
uv run pytest: 162 passed
uv run pytest --cov=backend --cov-report=term-missing: 162 passed, backend coverage 90.79%
uv run ruff check backend tests migrations: All checks passed
uv run alembic heads: 0002_task_queue_id (head)
docker compose config: passed
frontend npm run lint: passed
frontend npm run build: passed
npm audit --audit-level=high: found 0 vulnerabilities
uvx pip-audit: No known vulnerabilities found
```

## 关联文档

- 上一天：`day-28.md`
- 下一天：`day-30.md`
- 演示：`../supporting/demo-script.md`
- 简历：`../supporting/resume-story.md`
- 面试讲述：`../supporting/interview-story.md`
- 深度防守：`../supporting/interview-defense-dossier.md`
- 测试策略：`../supporting/testing-strategy.md`

## 建议提交

```text
docs: 整理 Day 29 演示与简历材料
```
