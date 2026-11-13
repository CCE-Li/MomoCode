# MomoCode 运维手册（阶段 14）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 14：部署与运维 |
| 版本 | v1.0 |
| 日期 | 2026-11-10 |
| 适用范围 | 单主机 Docker Compose 生产部署 |

---

## 1. 日常检查

```powershell
docker compose -f docker-compose.prod.yml ps
curl.exe -s http://127.0.0.1:8080/health/ready
```

关注：

- 四个服务是否 healthy：db、redis、api、web。
- `/health/ready` 的 `database` 与 `redis` 是否都为 `ok`。
- 磁盘剩余空间（PostgreSQL 数据 + 备份）。
- API/Web 日志是否有 5xx、认证失败激增、Redis 连接错误。

---

## 2. 日志

```powershell
docker compose -f docker-compose.prod.yml logs -f api
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f db
docker compose -f docker-compose.prod.yml logs -f redis
```

- API 日志包含 request_id；用户反馈错误时可据此定位。
- 不记录密码、Token、Cookie 或 OJ 凭据。
- 日志轮转：建议在宿主机配置 Docker `json-file` 的 `max-size`/`max-file`，或接入集中日志。
- 如接入 Sentry/Prometheus，需在部署层增加，不在 MVP 代码内硬编码。

---

## 3. 备份计划

建议：

- 每日全量备份；保留 7–30 天。
- 重大迁移前额外备份。
- 备份文件异地保存（对象存储/另一台主机）。
- 每月做一次恢复演练（恢复到临时库并校验计数）。

命令见 `docs/DEPLOYMENT.md` 第 8 节。

恢复演练检查：

```sql
SELECT count(*) FROM users;
SELECT count(*) FROM algorithms;
SELECT count(*) FROM skills;
SELECT count(*) FROM practice_tasks;
SELECT count(*) FROM practice_sessions;
SELECT count(*) FROM review_logs;
```

---

## 4. 数据库维护

```powershell
# 连接数据库
docker compose -f docker-compose.prod.yml exec db psql -U momocode -d momocode

# 查看连接数/大小
SELECT count(*) FROM pg_stat_activity;
SELECT pg_size_pretty(pg_database_size('momocode'));

# 查看迁移版本
docker compose -f docker-compose.prod.yml exec api alembic current
```

- 不在业务高峰期执行大表迁移。
- 破坏性变更前备份；优先“加新列 → 回填 → 切换 → 删除旧列”。
- 长期运行后按需执行 `VACUUM (ANALYZE)`；PostgreSQL 自动 vacuum 默认开启。
- 不手动修改 `alembic_version`。

---

## 5. Redis 维护

- Redis 用于登录/注册限流与短期缓存；不是事实来源。
- 检查：

```powershell
docker compose -f docker-compose.prod.yml exec redis redis-cli ping
docker compose -f docker-compose.prod.yml exec redis redis-cli info memory
```

- 如 Redis 故障：限流 fail-open 并记录 warning；登录仍可用但防护减弱。恢复后自动恢复限流。
- 不建议在 MVP 用 Redis 存唯一业务数据。

---

## 6. 内容更新

1. 修改 `content/seed/v2/` 下的 JSON，或修改 `content/source/` 手册后运行 `python -m scripts.build_manual_seed` 重建 JSON。
2. 更新 `manifest.json` 的 `version` 与 `description`。
3. 本地运行种子导入并检查校验。
4. 生产执行：

```powershell
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_content
```

5. 如内容需强制重放（谨慎）：

```powershell
docker compose -f docker-compose.prod.yml run --rm api python -m scripts.seed_content --force
```

6. 内容版本写入 `content_versions`；不要在数据库中手工改 slug。

---

## 7. 发布与回滚

发布：

```powershell
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d --wait
curl.exe -s http://127.0.0.1:8080/health/ready
```

回滚：

1. 若未涉及数据库迁移：回退镜像 tag 并 `up -d`。
2. 若涉及迁移：优先用兼容迁移回滚；必要时恢复备份。
3. 不要在未备份的情况下执行 `alembic downgrade`。

---

## 8. 安全运维

- 定期轮换 `SESSION_SECRET`；轮换会使现有会话失效，需提前通知。
- 不在聊天/日志/工单中粘贴 `.env.production`。
- 限制服务器 SSH 访问；数据库/Redis 不暴露公网端口。
- 监控依赖安全公告：
  - 前端：`npm audit --omit=dev`。
  - 后端：关注 FastAPI、SQLAlchemy、asyncpg、fsrs、cryptography 等安全更新。
- 生产必须：`ENVIRONMENT=production`、`SESSION_COOKIE_SECURE=true`、强 `SESSION_SECRET`。
- 建议增加 WAF/限流网关；应用内已有登录限流。
- CSP 已启用；如新增第三方脚本/字体，需同步更新 `deploy/nginx.conf`。

---

## 9. 故障处理

### 9.1 API 不健康

1. `docker compose -f docker-compose.prod.yml ps` 查看状态。
2. `logs api` 查看迁移/数据库/Redis 错误。
3. 检查 `.env.production` 的 `DATABASE_URL`、`REDIS_URL`。
4. 检查 db/redis 健康。
5. 修复后 `up -d --wait`。

### 9.2 登录失败/会话异常

- 检查系统时间与时区。
- 检查 `SESSION_COOKIE_SECURE` 与访问协议是否一致（HTTPS + true）。
- 检查 Cookie 是否被反向代理剥离。
- 检查 Redis 是否影响限流；限流失败不应阻止登录（fail-open）。

### 9.3 迁移失败

- 先停止 API，保留数据库。
- 查看 `alembic current` 与迁移日志。
- 从备份恢复或人工修复后重新迁移。
- 不要删除 `alembic_version` 绕过。

### 9.4 前端 404/白屏

- 检查 Nginx `try_files` 与 `dist` 是否复制成功。
- 检查 CSP 是否阻止新资源；浏览器控制台查看 CSP 报错。
- 检查 API 代理是否可达：`/api/v1/health`。

### 9.5 磁盘不足

- 检查 `docker system df`、PostgreSQL 数据大小、备份目录。
- 清理旧备份与无用镜像（谨慎）。
- 不要直接删除 PostgreSQL 数据目录。

---

## 10. 监控建议

MVP 至少：

- 外部 uptime 检查 `/health/ready` 与 `/`。
- 磁盘/内存/CPU 告警。
- API 5xx 与登录失败率。
- 备份任务成功/失败通知。

后续可接入：

- Prometheus + Grafana（请求延迟、错误率、DB 连接数）。
- Sentry（前端/后端异常）。
- 结构化日志集中存储与检索。

---

## 11. 数据保留与隐私

- 训练证据与 ReviewLog 默认长期保留，用于复习与统计。
- 用户删除策略 MVP 未开放；后续需实现级联删除或匿名化。
- 备份中可能包含用户邮箱与训练数据，需按敏感数据管理。
- 不把生产数据复制到测试环境；如需脱敏，先移除邮箱与凭据。
