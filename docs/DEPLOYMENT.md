# MomoCode 部署指南（阶段 14）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 14：部署与运维 |
| 版本 | v1.0 |
| 日期 | 2026-11-10 |
| 拓扑 | Nginx + FastAPI + PostgreSQL 16 + Redis 7（单主机 Docker Compose） |
| 状态 | 本地生产 Compose 已验证 |

---

## 1. 架构拓扑

```text
Browser
  │ HTTPS（生产） / HTTP:8080（本地验证）
  ▼
Nginx (web)
  ├── 静态资源 / SPA fallback
  ├── /api/      → FastAPI:8000
  └── /health/   → FastAPI:8000
                       │
                 ┌─────┴─────┐
                 ▼           ▼
            PostgreSQL      Redis
             (db)          (redis)
```

- 数据库与 Redis 只在 Docker 内部网络暴露，不映射到公网。
- API 容器启动时自动执行 `alembic upgrade head`。
- 前端静态文件由 Nginx 同源提供，API 同源代理，避免跨域 Cookie 问题。

---

## 2. 文件清单

| 文件 | 作用 |
|---|---|
| `deploy/backend.Dockerfile` | FastAPI 生产镜像（Python 3.13 + uv） |
| `deploy/frontend.Dockerfile` | Vue 构建 + Nginx 运行镜像 |
| `deploy/judge.Dockerfile` | C++ 自动判题镜像（非 root Alpine + g++） |
| `deploy/nginx.conf` | SPA、API 代理、安全响应头、CSP、gzip |
| `docker-compose.prod.yml` | 生产四服务编排 |
| `.env.production.example` | 生产环境变量模板 |
| `deploy/backup.sh` | 数据库备份脚本 |
| `deploy/restore.sh` | 数据库恢复脚本 |
| `docs/OPERATIONS.md` | 日常运维与故障处理 |

---

## 3. 环境准备

- Docker Engine 24+ 与 Docker Compose v2/v5
- 一台可运行容器的 Linux 主机（或本地 Docker Desktop 验证）
- 域名与 TLS 证书（生产）
- 足够磁盘空间存放 PostgreSQL 数据与备份

---

## 4. 配置环境变量

```powershell
Copy-Item .env.production.example .env.production
```

必须修改：

| 变量 | 说明 |
|---|---|
| `POSTGRES_PASSWORD` | 强密码；不要使用示例值。 |
| `DATABASE_URL` | 密码需与 `POSTGRES_PASSWORD` 一致；特殊字符需 URL 编码。 |
| `SESSION_SECRET` | 至少 64 位随机字符串；生产禁止默认值。 |
| `CORS_ORIGINS` | 生产域名，如 `["https://momo.example.com"]`。 |
| `ENVIRONMENT` | 生产设为 `production`。 |
| `SESSION_COOKIE_SECURE` | 生产必须为 `true`（HTTPS）。 |
| `APP_BASE_URL` | 前端公开地址，用于邮箱验证/重置链接。 |
| `EMAIL_BACKEND` | 生产必须为 `smtp`；本地可用 `console`。 |
| `SMTP_HOST` / `SMTP_PORT` | 生产 SMTP 服务。 |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP 凭据；不要提交到仓库。 |
| `SMTP_FROM` | 发件地址。 |
| `SMTP_USE_TLS` | 通常为 `true`（587 端口 STARTTLS）。 |
| `WEB_PORT` | 宿主机映射端口，默认 `8080`。 |

生产安全校验：

- `ENVIRONMENT=production` 时，若 `SESSION_SECRET` 仍为开发默认值，应用拒绝启动。
- 若 `SESSION_COOKIE_SECURE=false`，应用拒绝启动。
- 生产必须 `EMAIL_BACKEND=smtp` 且配置 `SMTP_HOST`，否则应用拒绝启动。

本地 HTTP 验证可使用：

```text
ENVIRONMENT=staging
SESSION_COOKIE_SECURE=false
CORS_ORIGINS=["http://localhost:8080"]
```

> 本地验证配置不能直接用于公网生产。

---

## 5. 构建与启动

```powershell
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --wait
docker compose -f docker-compose.prod.yml ps
```

启动顺序：

1. PostgreSQL/Redis 健康。
2. API 启动并执行 Alembic 迁移。
3. API 健康后启动 Web（Nginx）。

首次导入内容：

```powershell
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_content
```

重复导入会检测 version/checksum 并跳过；需要重放时加 `--force`：

```powershell
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_content --force
```

---

## 6. 健康检查

| 检查 | 地址 | 期望 |
|---|---|---|
| Nginx 健康 | `http://<host>:8080/healthz` | `ok` |
| API 就绪 | `http://<host>:8080/health/ready` | `database: ok`, `redis: ok` |
| API 存活 | `http://<host>:8080/health/live` | `status: ok` |
| API 健康 | `http://<host>:8080/api/v1/health` | `status: ok` |
| 前端 | `http://<host>:8080/` | 200 + SPA |

```powershell
curl.exe -s http://127.0.0.1:8080/health/ready
docker compose -f docker-compose.prod.yml ps
```

---

## 7. HTTPS 与反向代理

当前 Compose 的 Nginx 监听 80（本地验证）。生产建议：

1. 在宿主机或云负载均衡终止 TLS；或将证书挂载到 Nginx 并监听 443。
2. 将 HTTP 重定向到 HTTPS。
3. 生产 `CORS_ORIGINS` 使用 HTTPS 域名。
4. `SESSION_COOKIE_SECURE=true`。
5. Nginx 已配置：
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `Referrer-Policy: strict-origin-when-cross-origin`
   - `Permissions-Policy`
   - `Content-Security-Policy`（允许 self、data、blob worker；Monaco/ECharts 已验证）
6. 如需 HSTS，在确认全站 HTTPS 后增加：
   `add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;`

---

## 8. 数据备份与恢复

### 8.1 备份

Linux/macOS：

```bash
sh deploy/backup.sh
```

Windows PowerShell 等价命令：

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
$db = (docker compose -f docker-compose.prod.yml ps -q db).Trim()
docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc > /tmp/momocode-backup.dump'
docker cp "${db}:/tmp/momocode-backup.dump" "backups/momocode-$(Get-Date -Format yyyyMMddTHHmmssZ).dump"
```

### 8.2 恢复

```bash
sh deploy/restore.sh backups/momocode-20261110T173000Z.dump
```

恢复前务必确认目标数据库；`--clean --if-exists` 会删除同名对象。

### 8.3 验证记录

本地生产 Compose 已执行：

- 备份文件：`backups/momocode-prod-0008.dump`，130,798 bytes。
- 恢复到临时库 `momocode_restore`。
- 恢复后计数：algorithms=10、skills=40、practice_tasks=40、task_skills=81。
- 临时库已删除。

---

## 9. 迁移

- API 容器启动时自动执行 `alembic upgrade head`。
- 单实例部署可直接依赖启动迁移；多实例部署建议使用独立迁移 Job，避免并发。
- 破坏性迁移前必须备份。
- 迁移回滚：进入 API 容器执行 `alembic downgrade -1`（仅紧急/开发）。

```powershell
docker compose -f docker-compose.prod.yml exec api alembic current
docker compose -f docker-compose.prod.yml exec api alembic upgrade head
```

---

## 10. CI/CD

`.github/workflows/ci.yml` 执行：

- 后端：Ruff、格式检查、mypy、pytest。
- 前端：ESLint、vue-tsc、Vitest、生产构建、生产依赖审计。
- 图像构建：`deploy/backend.Dockerfile`、`deploy/frontend.Dockerfile`。
- E2E：GitHub Actions 启动 PostgreSQL/Redis 服务，执行迁移与种子，启动 API，Playwright 启动 Vite 并跑通注册 → 识别训练 → Analytics → 登出 → 登录、账号删除与修改密码。

生产发布流程建议：

1. CI 通过。
2. 备份数据库。
3. 拉取新镜像或重新构建。
4. `docker compose -f docker-compose.prod.yml up -d --wait`。
5. 检查 `/health/ready` 与关键页面。
6. 失败时回滚镜像版本并恢复备份（如涉及迁移）。

---

## 11. 本地生产验证记录

- `docker compose -f docker-compose.prod.yml build` 成功。
- 四服务 healthy：db、redis、api、web。
- `/health/ready` 返回 `database: ok`, `redis: ok`。
- 种子导入：3 分类、10 算法、40 技能、40 任务。
- 浏览器验证（Nginx:8080 + CSP）：
  - 注册/登录。
  - 模板训练 Monaco 编辑器加载。
  - 结果页与 Analytics 页面加载；ECharts 渲染 2 个 canvas。
- 安全响应头已确认存在。
- 备份/恢复计数一致。

---

## 12. 已知限制

- 当前为单机 Compose；未配置多副本、负载均衡或托管数据库。
- Nginx 默认监听 80；生产 TLS 需额外配置。
- 未接入外部监控/告警；见 `docs/OPERATIONS.md` 建议。
- Redis 限流在 Redis 故障时 fail-open。
- 自动判题当前通过 API 主机的 Docker 调用 `momocode-judge`；生产 API 容器未挂载 Docker socket。公网发布前需增加独立 judge worker/沙箱服务，否则编码任务会显示“判题容器启动失败/未判题”。
- 备份为手动/脚本触发；生产应配置定时任务与异地保存。
