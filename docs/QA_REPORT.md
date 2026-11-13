# MomoCode QA 报告（阶段 13）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 13：测试、质量与安全 |
| 版本 | v1.0 |
| 日期 | 2026-11-10 |
| 环境 | Windows 11、Python 3.13.14、Node 24.11.1、PostgreSQL 16、Redis 7 |
| 结论 | 核心流程通过；高危问题已处理；中等风险已记录，进入部署阶段 |

---

## 1. 测试范围

- 后端：认证、目录、训练会话、提示、四类训练、FSRS、OJ 手动关联与 Codeforces 同步、Analytics。
- 前端：登录/注册、路由守卫、算法库、技能详情、训练工作区、结果页、Smart Review、Analytics、Settings。
- 数据：Alembic 迁移、种子导入、用户数据隔离。
- 安全：CSRF、密码哈希、会话 Cookie、登录限流、OJ URL 白名单、SQL 参数化、XSS 面、密钥配置。
- E2E：真实浏览器注册、训练、复习、分析页、退出与账号删除。

---

## 2. 后端测试

命令：

```powershell
cd backend
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

结果：

| 检查 | 结果 |
|---|---|
| Ruff | 通过 |
| 格式 | 通过 |
| mypy | 通过（59 source files） |
| pytest | **60 passed** |

测试文件：

- `test_account_deletion.py`：密码错误拒绝、`DELETE` 确认校验、级联清理用户数据与登录失效。
- `test_auth.py`：注册、登录、登出、CSRF、未登录拒绝。
- `test_auth_sessions.py`：活跃会话、修改密码撤销其他设备、撤销单会话、退出所有设备、CSRF。
- `test_email_auth.py`：邮箱验证、重复令牌、过期令牌、密码重置撤销会话、未知邮箱不枚举。
- `test_catalog.py`：分类/算法/任务列表、筛选、详情、识别答案隐藏。
- `test_practice.py`：识别自动判分、部分/错误、模板、变体、纠错、提示、非法状态。
- `test_review.py`：正式复习更新 FSRS、自由练习不更新、到期队列、幂等。
- `test_oj.py`：Adapter 归一化、OJ 账号、手动提交、重复提交、Session 关联、URL/ID 校验、Codeforces 同步幂等/失败/归属。
- `test_analytics.py`：正确率、独立比例、提示依赖、趋势、错误分布、Skill Score、样本不足。
- `test_settings.py`：显示名、时区、每日上限、目标保留率、非法时区、CSRF、JSON 数据导出。
- `test_isolation.py`：跨用户 Session/Submission/OJ/Analytics/Review 隔离。
- `test_seed_content.py`：10 算法 / 40 技能 / 40 任务结构校验。

---

## 3. 前端测试

命令：

```powershell
cd frontend
npm run lint
npm run type-check
npm run test:unit
npm run build-only
```

结果：

| 检查 | 结果 |
|---|---|
| ESLint | 通过 |
| vue-tsc | 通过 |
| Vitest | **2 passed** |
| 生产构建 | 成功 |

说明：

- 组件测试覆盖空状态与 API 健康状态。
- 复杂页面通过 Playwright E2E 与 agent-browser smoke 验证；Playwright 已接入 CI。
- WorkspaceView 主包约 10KB，Monaco 独立 chunk 约 2.73MB 且仅编码任务加载；AnalyticsView 约 545KB（ECharts 按需引入）。

---

## 4. 数据库与迁移

命令：

```powershell
docker compose up -d --wait
cd backend
uv run alembic upgrade head
uv run python -m scripts.seed_content
```

结果：

| 项 | 结果 |
|---|---|
| 迁移链 | `0001 → 0014 (head)` |
| 表数量 | 17 张业务/迁移表 |
| 种子内容 | 3 分类、10 算法、40 技能、40 任务、81 条 task_skills |
| 重复导入 | 相同 version/checksum 跳过 |
| `--force` 重放 | 数据量不增加，无重复记录 |

已创建表：

`users`、`user_preferences`、`user_sessions`、`algorithm_categories`、`algorithms`、`skills`、`practice_tasks`、`task_skills`、`content_versions`、`practice_sessions`、`session_hints`、`skill_memories`、`review_logs`、`oj_accounts`、`submissions`、`user_skill_stats`。

---

## 5. 浏览器 E2E 记录

使用 `agent-browser` 与 Playwright 对真实前后端 + PostgreSQL/Redis 执行：

| 场景 | 结果 |
|---|---|
| 注册 → Dashboard 显示用户名 | 通过 |
| 登录 → Dashboard | 通过 |
| Library 展示 10 个算法 | 通过 |
| 算法详情 → 技能详情 | 通过 |
| 识别训练 → 自动判分“正确” → 结果页 | 通过 |
| 模板训练 → Monaco → Docker 自动判题 → 结果页测试用例 | 通过 |
| 纠错训练 → 模板 main 包装判题 + 错误类型 → 结果页 | 通过 |
| Settings → 时区/每日上限/目标保留率/显示名 | 通过（API + 页面） |
| 修改密码 → 其他设备会话被撤销 | 通过（双浏览器验证） |
| 邮箱验证 → 未验证提示消失 | 通过（浏览器 + 令牌） |
| 忘记密码 → 重置密码 → 新密码登录 | 通过（浏览器 + 令牌） |
| 账号删除 → 登录失效 → 数据清理 | 通过（Playwright E2E + 后端级联测试） |
| 修改密码 → 旧密码失效 → 新密码登录 | 通过（Playwright E2E） |
| OJ 手动关联 / Codeforces 同步 | 通过（实时 API：首次 100 新增，二次 100 跳过） |
| Analytics（ECharts core）与编码页（异步 Monaco） | 通过（2 canvas / 编辑器加载） |
| Smart Review → 到期队列 → 正式复习 → 下次复习时间 | 通过 |
| 复习后队列清空、今日已复习 +1 | 通过 |
| Analytics 页面 KPI、图表、样本不足、指标定义 | 通过 |
| 带 CSRF 的注册/Session 提交/退出回归 | 通过 |

截图检查：

- Dashboard：侧栏、卡片、主题、API 状态正常。
- 结果页：结果徽标、证据分列、参考实现折叠/展示正常。
- Analytics：KPI、样本不足提示、指标定义正常。

---

## 6. 安全核查

| 项 | 状态 | 说明 |
|---|---|---|
| 密码哈希 | 通过 | Argon2id；不返回 hash。 |
| 密码修改 | 通过 | 校验当前密码；撤销其他设备；当前会话保持。 |
| 会话管理 | 通过 | 活跃会话列表、撤销单会话、退出所有设备；不返回 token/IP 哈希。 |
| 会话 | 通过 | 服务端 opaque token，HttpOnly Cookie，令牌哈希存储。 |
| CSRF | 通过 | 双提交 Cookie + `X-CSRF-Token`；训练/OJ/登出写操作强制校验。 |
| 登录限流 | 通过（有残余风险） | Redis 固定窗口：登录 10 次/分钟、注册 5 次/小时；Redis 不可用时 fail-open 并记录 warning。 |
| 用户数据隔离 | 通过 | 所有 Session/Submission/Review/Analytics 查询带 `user_id`；隔离测试通过。 |
| SQL 注入 | 通过 | SQLAlchemy 参数化；仅健康检查使用固定 `SELECT 1`。 |
| XSS | 通过（当前面） | Vue 默认转义；题面以文本渲染，不使用 `v-html`；OJ URL 仅允许 http(s) 白名单域名。 |
| OJ 凭据 | 通过（MVP） | 不保存 OJ 密码；Codeforces 只读同步；`credentials_encrypted` 预留但未使用。 |
| OJ 同步 | 通过（有残余风险） | 手动触发、5 次/5 分钟、3 次重试、100 条上限；失败不写入；实时 API 验证通过。 |
| 密钥管理 | 通过 | 环境变量；生产环境拒绝默认 `SESSION_SECRET` 与不安全 Cookie。 |
| 日志泄漏 | 通过 | 不记录密码/Token/Cookie；500 只返回 request_id。 |
| CORS | 通过（需生产配置） | 开发允许 `http://localhost:5173`；生产通过环境变量配置。 |
| 生产依赖审计 | 通过 | `npm audit --omit=dev` = **0 vulnerabilities**。 |
| 开发依赖审计 | 残余风险 | 完整审计 14 个告警（12 moderate、2 critical，来自 Vitest 3 的 `tinypool`/`@vitest/mocker`），生产不受影响；升级 Vitest 5 需破坏性变更。 |

高危问题处理：

- Monaco 0.57 依赖的 DOMPurify 3.4.15 存在 critical XSS 公告；通过 npm `overrides` 固定到 **3.4.17**，生产审计清零。
- 训练/OJ 写操作补上 CSRF 强制校验，避免 Cookie 会话下的跨站写入。

---

## 7. 缺陷与残余风险

| 级别 | 问题 | 影响 | 处理 |
|---|---|---|---|
| 中 | 登录限流在 Redis 故障时 fail-open | 极端故障下暴力破解防护减弱 | 记录 warning；生产监控 Redis；后续可改为 fail-closed 或本地降级限流。 |
| 中 | Vitest 3 开发依赖有 critical 审计项 | 仅影响测试工具，不影响生产包 | 阶段 15 后升级 Vitest 5 / 重新评估测试栈。 |
| 中 | Monaco/Analytics 产物体积较大 | 首次进入工作区/分析页加载慢 | 已懒加载；可后续按需引入 ECharts 模块、Monaco 进一步裁剪。 |
| 中 | E2E 已接入 CI | CI 使用 Postgres/Redis 服务与 Chromium | 已解决；保留本地 agent-browser 作为补充 |
| 中 | CSP/安全响应头已配置 | Nginx 已启用 CSP、X-Frame-Options、nosniff、Referrer-Policy、Permissions-Policy | 已解决；生产仍需配置 TLS/HSTS |
| 低 | ~~无账号删除~~ | 已支持密码 + `DELETE` 确认的账号删除，级联清理训练/复习/OJ/统计数据 | 已解决 |
| 低 | 洛谷/AtCoder 同步未实现 | 目前仅 Codeforces 手动同步 | 后续按官方契约评估。 |

---

## 8. 验收结论

- 核心闭环（认证 → 目录 → 四类训练 → 证据 → FSRS → 复习 → OJ 手动关联/Codeforces 同步 → Analytics）已可运行并有自动化/浏览器验证。
- 高危安全问题（DOMPurify、CSRF 缺失）已处理。
- 中等风险不阻塞 MVP，但需在部署阶段处理安全响应头、备份与监控。
- **结论：可进入阶段 14 部署准备；发布前需完成部署验证与阶段 15 发布评审。**
