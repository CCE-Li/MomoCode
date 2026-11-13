# MomoCode

MomoCode 是一个**算法识别与代码模板肌肉记忆训练平台**。它不追求做题数量，而是帮助用户长期记住算法、识别适用场景、独立复现模板、掌握变体并针对薄弱点纠错。

核心闭环：

```
学习算法 → 算法识别 → 模板复现 → 变体/纠错 → OJ 评测
  → 记录行为证据 → 技能评估 → FSRS 更新 → 下次复习
```

## 当前状态

- 阶段 1–4：PRD、架构、数据库、UI/UX（已完成）
- 阶段 5–7：仓库骨架、后端基础、前端与认证（已完成）
- 阶段 8–12：算法内容、训练引擎、FSRS、OJ 手动关联、Analytics（已完成）
- 阶段 13–15：QA、部署、MVP 发布评审（已完成）
- 当前版本：MVP v0.1.0；功能验收通过，公网发布需完成 TLS/监控/定时备份等部署前置项

当前系统包含：Vue 3 前端、FastAPI + PostgreSQL + Redis、Alembic 迁移、多用户邮箱密码认证、算法内容种子、四类训练、FSRS 复习、OJ 手动关联、Analytics 与 Settings。生产 Compose、Nginx、CSP、备份恢复与发布文档已就绪。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3、TypeScript、Vite、Pinia、Vue Router |
| 后端 | Python 3.13、FastAPI、Pydantic v2、SQLAlchemy 2、Alembic |
| 数据库 | PostgreSQL 16 |
| 缓存/限流 | Redis 7 |
| 测试 | pytest、httpx、Vitest、Vue Test Utils |
| 工程 | uv、ESLint、Prettier、Ruff、mypy、GitHub Actions |

## 目录结构

```text
.
├── backend/            # FastAPI 应用、测试、Alembic 迁移、种子导入脚本
├── frontend/           # Vue 3 应用
├── content/            # 算法内容种子（categories/algorithms/skills/tasks）
├── docs/               # PRD、架构、数据库、UI/UX、开发说明
├── deploy/             # 部署配置（阶段 14）
├── scripts/            # 种子导入/开发脚本（阶段 8+）
├── docker-compose.yml  # PostgreSQL + Redis
└── .github/workflows/  # CI
```

## 环境要求

- Node.js >= 20.19（本仓库在 Node 24 上验证；脚手架工具自身可能提示需要 24.12，不影响项目运行）
- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- Docker Desktop（用于 PostgreSQL/Redis；仅跑健康检查时可暂不启动）
- Git

## 快速开始

### 1. 后端

```powershell
cd backend
Copy-Item .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

验证：

- <http://localhost:8000/health/live>
- <http://localhost:8000/health/ready>（需要 PostgreSQL/Redis）
- <http://localhost:8000/api/v1/health>
- OpenAPI：<http://localhost:8000/docs>

### 2. 前端

```powershell
cd frontend
Copy-Item .env.example .env
npm install
npm run dev
```

打开 <http://localhost:5173>。Vite 已将 `/api` 与 `/health` 代理到 `http://localhost:8000`。

### 3. PostgreSQL / Redis（阶段 6 起需要）

确保 Docker Desktop 已启动，然后：

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
docker build -t momocode-judge:latest -f deploy/judge.Dockerfile deploy
```

`momocode-judge` 用于自动编译运行 C++ 并对比内置测试用例；未构建时编码提交会显示“判题服务不可用”。

停止：

```powershell
docker compose down
```

> Docker Compose 已在阶段 6 验证；验证完成后已停止服务。需要数据库时重新执行 `docker compose up -d`。

## 常用命令

### 后端

| 命令 | 作用 |
|---|---|
| `uv sync` | 安装依赖 |
| `uv run alembic upgrade head` | 应用数据库迁移 |
| `uv run alembic revision --autogenerate -m "message"` | 生成迁移（先确认模型） |
| `uv run alembic downgrade -1` | 回滚一步（仅开发/紧急） |
| `uv run python -m scripts.seed_content` | 导入算法内容种子（幂等） |
| `uv run python -m scripts.seed_content --force` | 强制重放当前内容版本 |
| `uv run uvicorn app.main:app --reload --port 8000` | 开发服务器 |
| `uv run pytest` | 单元/集成测试 |
| `uv run ruff check .` | Lint |
| `uv run ruff format --check .` | 格式检查 |
| `uv run mypy app` | 类型检查 |

### 前端

| 命令 | 作用 |
|---|---|
| `npm install` | 安装依赖 |
| `npm run dev` | 开发服务器 |
| `npm run lint` | ESLint |
| `npm run type-check` | Vue/TS 类型检查 |
| `npm run test:unit` | Vitest |
| `npm run build` | 类型检查 + 生产构建 |
| `npm run format` | Prettier |

## 验证记录（2026-11-10）

| 检查 | 命令 | 结果 |
|---|---|---|
| 后端依赖 | `uv sync` | 成功（Python 3.13.14） |
| 后端 Lint | `uv run ruff check .` | 通过 |
| 后端格式 | `uv run ruff format --check .` | 通过 |
| 后端类型 | `uv run mypy app` | 通过 |
| 后端测试 | `uv run pytest` | 57 passed |
| 数据库/Redis | `docker compose up -d --wait` | PostgreSQL 16、Redis 7 healthy |
| PostgreSQL 迁移 | `uv run alembic upgrade head` | `20261111_0009 (head)`；17 张表 |
| 内容导入 | `uv run python -m scripts.seed_content` | 3 分类、10 算法、40 技能、40 任务、81 条 task_skills |
| 导入幂等 | 重复执行 seed | 检测到相同版本/checksum，跳过 |
| 就绪检查 | `GET /health/ready` | `database: ok`, `redis: ok` |
| 认证闭环 | 真实 API smoke test | 注册 201 → me 200 → logout 204 → me 401 → login 200 |
| FSRS 闭环 | 真实 API smoke test | 正式复习 → 下次复习时间；逾期队列返回 |
| OJ 手动关联 | 真实 API smoke test | 创建账号/提交/去重/关联 Session |
| Analytics | 真实 API + 浏览器 | KPI、趋势、错误分布、Skill Score、样本不足、Fibonacci vs 我的遗忘曲线 |
| 测试运行 | 真实 API + 浏览器 | 题目样例用例 + 自定义输入/期望输出 + Docker 运行结果 |
| 模板/变体/纠错训练 | 真实 API + 浏览器 | Monaco + Vim 模式、提交后 Docker 自动判题、结果页展示测试用例 |
| AI 判题 | 真实 API + 浏览器 | 题面 + 参考实现 + 用户代码 → LLM 结论/问题/建议；需配置 `LLM_API_KEY` |
| Settings | 真实 API | 显示名、时区、每日上限、目标保留率、主题同步、OJ 账号、数据导出、账号删除 |
| 邮箱验证/找回密码 | 浏览器 + API | 验证链接、未验证提示、重置密码撤销所有会话 |
| 浏览器训练闭环 | `agent-browser` + Playwright | 注册 → 识别/模板/纠错 → 结果页；Smart Review；Analytics |
| Playwright E2E | `npm run test:e2e` | 4 passed（Galaxy + 训练闭环 + 账号删除 + 修改密码） |
| 生产部署 | `docker compose -f docker-compose.prod.yml` | db/redis/api/web 全部 healthy；CSP 下 Monaco/ECharts 正常 |
| 备份恢复 | `pg_dump` + `pg_restore` | 130,798 bytes；恢复后 10/40/40/81 |
| 生产依赖审计 | `npm audit --omit=dev` | 0 vulnerabilities |
| 前端依赖 | `npm install` | 成功 |
| 前端 Lint | `npm run lint` | 通过 |
| 前端类型 | `npm run type-check` | 通过 |
| 前端测试 | `npm run test:unit` | 2 passed |
| 前端构建 | `npm run build-only` | 成功 |
| 浏览器认证闭环 | `agent-browser` | 注册 → Dashboard（显示 Browser Smoker）→ 退出 → 登录 → Dashboard |
| 视觉检查 | Dashboard 截图 | 侧栏、卡片、主题、API 状态正常 |
| 运行时 | `uvicorn` + `vite` + curl | `/health/live`、`/api/v1/health`、Vite 代理均返回 200 |

未验证项/残余风险：

- 公网 TLS、外部监控与定时异地备份需在部署环境配置；本地生产 Compose 已通过 HTTP 验证。
- `npm audit --omit=dev` 为 0 漏洞；完整审计有 14 个 dev 依赖告警（含 2 个 critical，来自 Vitest 3 的 `tinypool`/`@vitest/mocker`），生产不受影响，后续升级测试栈。

## 文档

- [PRD](docs/PRD.md)
- [系统架构](docs/ARCHITECTURE.md)
- [数据库与领域模型](docs/DATABASE.md)
- [UI/UX](docs/UI_UX.md)
- [算法内容规范](docs/ALGORITHM_CONTENT_SPEC.md)
- [OJ 集成说明](docs/OJ_INTEGRATION.md)
- [邮箱验证与密码重置](docs/EMAIL_AUTH.md)
- [Analytics 指标口径](docs/ANALYTICS_METRICS.md)
- [QA 报告](docs/QA_REPORT.md)
- [部署指南](docs/DEPLOYMENT.md)
- [运维手册](docs/OPERATIONS.md)
- [发布检查清单](docs/RELEASE_CHECKLIST.md)
- [MVP 发布报告](docs/MVP_RELEASE_REPORT.md)
- [开发说明](docs/DEVELOPMENT.md)
- 阶段提示词：[`MomoCode_AI_Prompts/`](MomoCode_AI_Prompts/)

## 重要规则

- Algorithm、Skill、PracticeTask 是不同实体。
- 每个用户 × 每个 Skill 独立维护 FSRS 状态。
- 一次 AC 不等于掌握；WA 也不一定代表遗忘。
- 自由练习默认不更新 FSRS；明确标记正式复习才更新。
- 提示等级 0–5；识别训练只启用 0–3。
- 不自建判题服务器；MVP 的 OJ 能力只有手动关联与题目跳转。
- Skill Score 与 FSRS Difficulty 不得混用。
- 不提交真实密钥；`.env` 已被忽略。

## 已知限制（MVP v0.1.0）

- 公网发布前需配置 TLS/HTTPS、生产 Secrets、SMTP、监控与定时异地备份。
- 已支持账号删除（密码 + `DELETE` 确认，级联清理训练/复习/OJ/统计数据）；邮箱验证不阻塞登录。
- 作答区使用 Monaco，可切换 Vim 模式（Normal/Insert/Visual、`:` 命令与状态栏）；这是 Neovim 键位模拟，不是真正的 Neovim 终端。原生 Neovim 需要额外的 PTY/WebSocket 编辑器服务。
- AI 判题需要配置 OpenAI 兼容的 `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`；未配置时按钮会提示不可用，不影响内置测试用例判题。
- 编码任务采用内置测试用例自动判题；当前 30 个编码任务均配置了判题用例。生产环境的 API 容器还需要独立判题 worker 或受控 Docker 访问，不能直接在公网 API 容器挂 Docker socket。
- 无第三方登录（Provider 抽象已预留）。
- 无 OJ 提交同步（仅 Codeforces 手动同步）；洛谷/AtCoder 同步未实现。
- 单实例部署；多实例需独立迁移 Job 与共享基础设施。
- Monaco 编码页 chunk 约 2.7MB，仅在编码任务异步加载；Analytics 已按需引入 ECharts。
- 登录限流在 Redis 故障时 fail-open。
- UI 采用深色夜间工业风（近黑炭灰 + 橙色强调），默认深色；浅色仍可切换。
