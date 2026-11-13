# 开发说明

本文档记录本地开发环境、命令、约定与阶段工作流。架构与业务规则见 `docs/ARCHITECTURE.md` 与 `docs/PRD.md`。

## 1. 环境

| 工具 | 版本 | 说明 |
|---|---|---|
| Node.js | >= 20.19（在 24.11 验证） | 前端构建与测试 |
| npm | 11.x | 锁定依赖 |
| Python | 3.13 | 后端运行时 |
| uv | 0.12+ | 依赖与虚拟环境 |
| Docker | 29.x | PostgreSQL/Redis |
| Git | 2.55+ | 版本控制 |

### 1.1 环境变量

后端：

```powershell
cd backend
Copy-Item .env.example .env
```

前端：

```powershell
cd frontend
Copy-Item .env.example .env
```

根目录（Docker Compose）：

```powershell
Copy-Item .env.example .env
```

`.env` 不提交；只提交 `.env.example`。

## 2. 启动

### 2.1 后端

```powershell
cd backend
Copy-Item .env.example .env
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

- 健康检查：`GET http://localhost:8000/health/live`
- 就绪检查：`GET http://localhost:8000/health/ready`（需要 PostgreSQL/Redis）
- API 健康：`GET http://localhost:8000/api/v1/health`
- OpenAPI：`http://localhost:8000/docs`

认证 API：

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/register` | 注册并设置会话/CSRF Cookie |
| POST | `/api/v1/auth/login` | 登录并设置会话/CSRF Cookie |
| POST | `/api/v1/auth/logout` | 需要会话 + `X-CSRF-Token` |
| GET | `/api/v1/auth/me` | 当前用户 |

### 2.2 前端

```powershell
cd frontend
npm install
npm run dev
```

- 地址：`http://localhost:5173`
- `/api` 与 `/health` 由 Vite 代理到 `http://localhost:8000`
- 若后端未启动，Dashboard 的 API 状态会显示“API 不可达”，这是预期行为。

### 2.3 数据库与 Redis

```powershell
Copy-Item .env.example .env
docker compose up -d
docker compose ps
```

端口：

- PostgreSQL：`5432`
- Redis：`6379`

停止：

```powershell
docker compose down
```

删除数据卷（谨慎，会清空本地数据）：

```powershell
docker compose down -v
```

> 阶段 6 已加入 SQLAlchemy 连接、`/health/ready`、Alembic 迁移与认证基础。首次启动前必须执行 `uv run alembic upgrade head`。迁移命令见 2.4。

### 2.4 数据库迁移

```powershell
cd backend
uv run alembic current
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "describe change"
```

规则：

- 迁移文件在 `backend/alembic/versions/`。
- 生成 autogenerate 后必须人工检查，尤其是约束名、索引与数据迁移。
- 生产环境迁移前备份；破坏性变更先加新列、回填、再删旧列。
- 当前首个迁移：`20261110_0001_auth_foundation`（users、user_preferences、user_sessions）。

### 2.5 前端认证与 CSRF

- `src/api/auth.ts` 封装登录、注册、当前用户、登出；页面不直接调用 `fetch`。
- `src/stores/auth.ts` 维护 `user/initialized/loading/error`；首次导航调用 `fetchMe()` 恢复会话。
- `src/router/index.ts` 的守卫保护 `requiresAuth` 路由；已登录访问登录页会跳回 Dashboard。
- 会话使用 HttpOnly Cookie；CSRF Cookie 由后端设置，API Client 对非 GET 请求自动附加 `X-CSRF-Token`。
- 登录/注册成功后会建立会话；退出会撤销服务端会话并清除 Cookie。
- 401 时路由守卫会把用户送回登录页，并保留 `redirect` 参数。

### 2.6 算法内容种子

生产导入使用 `content/seed/v2/`（`v1` 保留为稳定测试基线）：

- `manifest.json`：版本、说明、文件列表。
- `categories.json`：7 个分类。
- `algorithms.json`：37 个算法（含 ICPC/CCPC 手册的全部章节）。
- `skills.json`：94 个技能。
- `tasks.json`：200 个训练任务，其中 106 个为 `oj_reference` 模板题任务。

手册原文在 `content/source/MomoCode_ICPC_CCPC_算法知识点手册.md`。修改手册或映射后重新生成内容包：

```powershell
cd backend
uv run python -m scripts.build_manual_seed
uv run python -m scripts.seed_content --force
```

生成器只负责解析手册并写 JSON；数据库写入仍由 `scripts.seed_content` 完成。

前端：

```powershell
cd frontend
npm run lint
npm run type-check
npm run test:unit
npm run build-only
npm run test:e2e
```

`test:e2e` 使用 Playwright；本地需要 API 在 8000 运行，Vite 由 Playwright 自动启动（也可先启动并复用）。CI 中由 `.github/workflows/ci.yml` 的 `e2e` job 启动 PostgreSQL/Redis、API 与 Vite。

导入：

```powershell
docker compose up -d --wait
docker build -t momocode-judge:latest -f deploy/judge.Dockerfile deploy
cd backend
uv run alembic upgrade head
uv run python -m scripts.seed_content
uv run python -m scripts.seed_content --force
```

### 2.7 自定义复习内容

用户可以把自己想复习的笔记、模板或错题结论加入 FSRS 队列：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/reviews/custom-items` | 列出当前用户的自定义内容；`include_inactive=true` 含已移除项 |
| POST | `/api/v1/reviews/custom-items` | 创建内容并立即进入到期队列 |
| PATCH | `/api/v1/reviews/custom-items/{id}` | 修改标题/内容/标签/来源或软删除/恢复 |
| DELETE | `/api/v1/reviews/custom-items/{id}` | 软删除（历史 ReviewLog 保留） |
| POST | `/api/v1/reviews/custom-items/{id}/review` | 以 Rating 1–4 完成一次复习，更新 FSRS |

- 写操作需要 CSRF；所有查询按 `user_id` 隔离。
- `GET /reviews/due`、`/reviews/today`、`/reviews/history` 已合并技能与自定义内容。
- 自定义内容不展示 FSRS `difficulty/stability`，只展示到期时间与评分结果。

### 2.8 用户自建题目

登录用户可以在 `/practice/user-tasks` 页面添加自己的 OJ 题或原创训练题。后端入口：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/user-tasks` | 列出当前用户的自建题目 |
| POST | `/api/v1/user-tasks` | 创建单道题目 |
| POST | `/api/v1/user-tasks/import` | 批量导入，最多 50 道；任一道失败整批不写入 |
| GET | `/api/v1/user-tasks/{id}` | 查看自己的题目详情 |
| PATCH | `/api/v1/user-tasks/{id}` | 更新题目 |
| DELETE | `/api/v1/user-tasks/{id}` | 软删除；历史 Session 保留 |

导入字段与 `content/seed/v2/tasks.json` 基本一致，但不传 `slug`/`source_type`：

- 必填：`title`、`statement_md`、`target_skills`（技能 slug 列表）。
- 常用：`training_type`、`evaluation_mode`、`difficulty`、`oj_platform`、`oj_problem_ref`、`oj_problem_url`、`constraints_md`、`code_scaffold`、`reference_solution_md`、`hints`、`max_hint_level`、`tags`。
- `tags` 支持 `#二分`、`#双指针`、`#BFS` 或逗号分隔；服务层去 `#`、去重并限制为 12 个。
- `source_type` 固定写入 `user`，`created_by_user_id` 固定为当前用户；公共 `/catalog/tasks` 不会返回自建题目。
- 列表支持 `?tag=二分` 过滤；公共标签统计入口为 `GET /api/v1/catalog/tags`。
- 关联 OJ 时 `oj_platform` 与 `oj_problem_ref` 必须同时提供，URL 必须是 http/https。
- 识别题必须使用 `evaluation_mode='auto_recognition'` 且 `max_hint_level<=3`；`auto_tests` 必须在 `expected_output_spec.judge` 提供测试用例。

### 2.9 无内置判题用例的任务

`oj_reference` 与 `template` 任务通常没有 `expected_output_spec.judge`。这类任务在提交时必须提供 `self_assessment`（`correct/partial/incorrect`）；判题返回 `ungraded` 时，FSRS 映射会回退到自评，而不是直接判为 Again。

判题：

- 本地 API 通过 Docker 调用 `momocode-judge:latest`，镜像内为非 root Alpine + g++。
- 判题容器 `--network none`、只读根文件系统、tmpfs、CPU/内存/进程/时间限制。
- 判题容器限制：禁网、只读根文件系统、非 root、CPU/内存/进程数/时间限制。
- 作答区 Vim 模式由 `monaco-vim` 提供；Vite alias 将 `monaco-editor/esm/vs/editor/editor.api` 映射到当前 Monaco 实例，避免重复打包。
- 后端测试会自动 mock `judge_cpp`，CI 不依赖 Docker 判题镜像。
- 修改 `content/seed/v2/tasks.json` 中的 `expected_output_spec.judge` 后需重新导入内容。

规则：

- 导入按 slug upsert，任务技能关联先删后建。
- 相同 `version + checksum` 默认跳过；`--force` 强制重放。
- 内容版本写入 `content_versions`。
- 详细规范见 `docs/ALGORITHM_CONTENT_SPEC.md`。

## 3. 质量命令

### 后端

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

### 前端

```powershell
cd frontend
npm run lint
npm run type-check
npm run test:unit
npm run build
```

## 4. 代码约定

### 4.1 后端

- 路由只做 HTTP 适配；业务规则放 `modules/*/service.py`。
- 所有用户资源查询必须带 `user_id` 作用域（公共内容除外）。
- Pydantic 模型负责输入/输出校验；ORM 模型不直接返回前端。
- 数据库变更必须通过 Alembic。
- 不在日志中输出密码、Token、Cookie、OJ 凭据。
- 时间统一 UTC；用户时区只用于展示与跨日计算。

### 4.2 前端

- API 请求集中在 `src/api/`；页面不直接 `fetch`。
- 服务端数据以 API 为准，不在 Pinia 中长期缓存权威数据。
- 组件必须覆盖 idle/hover/focus/loading/error/disabled 状态（适用时）。
- 表单必须有可见 label；错误与字段关联。
- 颜色使用 `src/styles/tokens.css`；不硬编码主题色。
- 不在前端展示 FSRS Difficulty/Stability。
- 不把一次 AC 描述为“掌握”。

### 4.3 提交前检查

至少运行：

```powershell
cd backend
uv run ruff check .; uv run mypy app; uv run pytest

cd ..\frontend
npm run lint; npm run type-check; npm run test:unit
```

> 如果命令失败，先修复，不要删除有效断言来“修绿”。

## 5. 阶段工作流

1. 一次只执行一个阶段。
2. 设计阶段先更新 `docs/`，确认后再编码。
3. 阶段结束更新 README/开发文档，并记录真实测试结果。
4. 数据模型变更必须有迁移；关键业务逻辑必须有测试。
5. 不提前实现后续阶段，不虚构 API/依赖/字段。

## 6. 常见问题

### 6.1 Docker 连接失败

错误示例：

```
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

处理：

1. 启动 Docker Desktop。
2. 等待引擎就绪。
3. 重新执行 `docker compose up -d`。

### 6.2 前端 Node 版本警告

`create-vue` 脚手架工具自身可能要求 Node >= 24.12，但本项目的 `engines` 为 `>=20.19`，在 Node 24.11 上可运行。若 `npm install` 报 engine 错误，可升级 Node 或使用 `npm install --engine-strict=false`（仅本地临时）。

### 6.3 端口冲突

- 后端 8000：`uv run uvicorn ... --port 8001`，并同步修改 `frontend/vite.config.ts` 代理。
- 前端 5173：Vite 会自动选择下一个端口；代理仍指向 8000。
- PostgreSQL 5432 / Redis 6379：修改根目录 `.env` 的 `POSTGRES_PORT`/`REDIS_PORT`，并同步后端 `DATABASE_URL`/`REDIS_URL`。

### 6.4 API 状态显示不可达

1. 确认后端正在 8000 端口运行。
2. 直接访问 `http://localhost:8000/api/v1/health`。
3. 检查 Vite 代理配置。
4. 检查浏览器控制台/CORS（开发环境已允许 `http://localhost:5173`）。

## 7. 阶段状态

- 阶段 1–4：需求、架构、数据库、UI/UX（已完成）。
- 阶段 5–7：仓库骨架、后端基础、前端与认证（已完成）。
- 阶段 8：算法内容与种子数据（已完成）。
- 阶段 9：四类训练引擎（已完成）。
- 阶段 10：FSRS 与复习队列（已完成）。
- 阶段 11：OJ 手动关联与 Adapter 契约（已完成）。
- 阶段 12：Analytics 与指标口径（已完成）。
- 阶段 13：测试、安全与 QA（已完成，见 `docs/QA_REPORT.md`）。
- 阶段 14：部署与运维（已完成，见 `docs/DEPLOYMENT.md`、`docs/OPERATIONS.md`）。
- 阶段 15：发布评审（已完成，见 `docs/RELEASE_CHECKLIST.md`、`docs/MVP_RELEASE_REPORT.md`）。

当前为 MVP v0.1.0；公网发布前需完成 TLS、生产 Secrets、监控与定时异地备份。
