# MomoCode MVP 发布检查清单（阶段 15）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 15：MVP 发布评审 |
| 版本 | v1.0 |
| 日期 | 2026-11-10 |
| 依据 | `docs/PRD.md`、`docs/ARCHITECTURE.md`、`docs/DATABASE.md`、`docs/QA_REPORT.md`、`docs/DEPLOYMENT.md` |
| 状态标记 | ✅ 通过 · ⚠️ 部分通过 · ⛔ 阻塞 · ⬜ 未验证 |

---

## 1. 验收场景总览

| 场景 | 状态 | 证据 |
|---|---|---|
| 用户登录与数据持久化 | ✅ | 浏览器注册/登录；PostgreSQL 验证；`test_auth.py`、`test_isolation.py` |
| 浏览算法/技能/任务 | ✅ | Library/Algorithm/Skill 页面；10 算法 / 40 技能 / 40 任务 |
| 完成四类训练 | ✅ | 识别、模板、变体、纠错后端测试；识别/模板/纠错浏览器验证 |
| 记录提示、耗时、错误与证据 | ✅ | Session/Hint/Result；`test_practice.py`、`test_settings.py` |
| 正式复习更新对应 Skill 的 FSRS | ✅ | `test_review.py`；真实 PostgreSQL smoke；浏览器 Smart Review |
| 自由练习默认不污染 FSRS | ✅ | `test_review.py::test_free_practice_does_not_update_fsrs` |
| 生成今日复习任务 | ✅ | `/api/v1/reviews/due`；浏览器 Smart Review |
| OJ 提交可同步或手动关联 | ✅ | 手动关联 + Codeforces 手动同步；其他平台未实现 |
| 统计与实际数据一致 | ✅ | `test_analytics.py`；浏览器 Analytics；无假数据 |
| Settings 管理账号/偏好/OJ/时区 | ✅ | `/settings` API + 页面；时区/上限/目标保留率/显示名/OJ |
| 生产部署可重复 | ✅（单机） | 生产 Compose、镜像、健康检查、Nginx、备份恢复验证 |
| 公网 HTTPS/监控/定时备份 | ⚠️ | 文档与配置已准备；TLS/监控/定时任务需部署时配置 |

---

## 2. 功能清单

### 2.1 认证与用户

- ✅ 邮箱密码注册/登录/登出。
- ✅ 修改密码；修改后撤销其他设备，当前会话保持登录。
- ✅ 活跃会话列表、撤销单个会话、退出所有设备。
- ✅ 邮箱验证（token 24h、可重发、不阻塞登录）。
- ✅ 找回密码（token 1h、重置后撤销全部会话、未知邮箱不枚举）。
- ✅ HttpOnly 会话 Cookie + CSRF 双提交。
- ✅ Argon2id 密码哈希。
- ✅ 用户数据隔离（Session/Submission/Review/Analytics/OJ）。
- ✅ 登录/注册 Redis 限流（fail-open 有记录）。
- ✅ 账号删除：密码 + `DELETE` 确认，级联清理训练、复习、OJ、统计与登录数据。
- ⚠️ 第三方登录预留 Provider 抽象，未实现。

### 2.2 算法库

- ✅ 3 分类 / 10 算法 / 40 技能 / 40 任务。
- ✅ Category → Algorithm → Skill 浏览与检索。
- ✅ 技能目标、掌握证据、易错点。
- ✅ 任务按算法/技能/训练类型/难度筛选。
- ✅ 识别任务不提前暴露目标技能。

### 2.3 四类训练

| 训练 | 后端 | 前端 |
|---|---|---|
| 识别 | ✅ 自动判分（正确/部分/错误） | ✅ 多选 + 即时判分 + 结果页 |
| 模板 | ✅ 内置测试自动判题 + 可选 OJ | ✅ Monaco + 自动判题 + 参考实现 |
| 变体 | ✅ 内置测试自动判题 + 变体证据 | ✅ 同一编码工作区（后端测试验证） |
| 纠错 | ✅ 模板 main 包装判题 + 错误类型 | ✅ 缺陷代码 + 错误类型 + 结果 |

- ✅ Session 状态机：created → in_progress → submitted → completed。
- ✅ 非法状态转换拒绝（409）。
- ✅ 提示 0–5 级；识别 0–3；每级记录一次。
- ✅ 内置判题结果与 OJ 证据分列。

### 2.4 FSRS

- ✅ `fsrs` 6.3.2；SkillMemory 以 user × skill 唯一。
- ✅ 正式复习更新 state/step/stability/difficulty/due。
- ✅ 自由练习默认不更新。
- ✅ 完成后重复提交幂等，ReviewLog 唯一 session_id。
- ✅ 到期队列、今日统计、每日上限、用户时区。
- ✅ 结果页显示下次复习时间。
- ✅ FSRS Difficulty 不作为 Skill Score 展示。

### 2.5 OJ

- ✅ OJ 账号元数据（平台 + handle），不保存密码。
- ✅ 手动录入 Submission，平台/提交 ID/Verdict/语言/耗时/内存/时间。
- ✅ 幂等去重；平台缺失字段 null。
- ✅ Submission 关联 Session；重复/跨会话关联冲突处理。
- ✅ 题目 URL 域名白名单（Codeforces/洛谷/AtCoder）。
- ✅ Codeforces 手动同步：最多 100 条、幂等去重、失败不写入、5 次/5 分钟。
- ✅ `OJAdapter` 契约与 Manual Adapter。
- ⚠️ 洛谷/AtCoder 同步未实现。
- ✅ 一次 AC 不自动等于掌握。

### 2.6 Analytics

- ✅ 正确率、独立完成比例、提示依赖、归一化耗时。
- ✅ 训练类型分布、错误类型分布、复习状态。
- ✅ Skill Score v0（0–100，样本量、样本不足、初步数据）。
- ✅ 指标定义 API 与页面。
- ✅ 无数据/样本不足明确标注，不使用假数据。
- ⚠️ Skill Score 权重为 v0，后续可迭代。

### 2.7 Settings

- ✅ 显示名更新。
- ✅ 时区（IANA 校验）、每日复习上限、目标保留率。
- ✅ OJ 账号添加/移除。
- ✅ 主题本地切换。
- ⚠️ 邮箱只读；已支持密码修改/账号删除。

---

## 3. 非功能检查

| 项 | 状态 | 说明 |
|---|---|---|
| 后端单元/集成测试 | ✅ | 57 passed |
| 前端 Lint/类型/单测/构建 | ✅ | ESLint、vue-tsc、2 component tests、build |
| 用户隔离 | ✅ | `test_isolation.py` |
| CSRF | ✅ | 训练/OJ/Settings/登出写操作强制校验 |
| 生产依赖审计 | ✅ | `npm audit --omit=dev` = 0 |
| 开发依赖审计 | ⚠️ | 14 个 dev 告警（2 critical，Vitest/tinypool），生产不受影响 |
| 迁移 | ✅ | 0001–0009 在 PostgreSQL 16 验证 |
| 种子导入 | ✅ | 幂等；`--force` 无重复 |
| 备份/恢复 | ✅ | 130,798 bytes 备份；恢复后计数 10/40/40/81 |
| 生产 Compose | ✅ | db/redis/api/web 全部 healthy |
| Nginx 安全头 | ✅ | CSP、X-Frame-Options、nosniff、Referrer-Policy、Permissions-Policy |
| CSP 下 Monaco/ECharts | ✅ | 浏览器验证；ECharts 渲染 2 canvas |
| HTTPS/TLS | ⚠️ | 本地验证 HTTP；生产需配置证书与 Secure Cookie |
| 外部监控/告警 | ⚠️ | 文档建议；未接入 |
| 定时/异地备份 | ⚠️ | 脚本与流程已备；未配置生产定时任务 |
| E2E 纳入 CI | ✅ | Playwright Chromium；CI 使用 Postgres/Redis 服务，4 tests passed |

---

## 4. 发布阻塞项（公网发布前必须完成）

1. **TLS/HTTPS**：配置证书与 443；HTTP 重定向 HTTPS。
2. **生产 Secrets**：强 `SESSION_SECRET`、DB 密码、`ENVIRONMENT=production`、`SESSION_COOKIE_SECURE=true`。
3. **CORS 域名**：改为真实 HTTPS 域名。
4. **备份**：配置每日定时备份 + 异地保存 + 恢复演练记录。
5. **监控**：至少 uptime 检查 `/health/ready` 与 `/`，以及 5xx/登录失败/磁盘告警。
6. **SMTP**：生产必须 `EMAIL_BACKEND=smtp`，配置 `SMTP_HOST`/凭据/发件地址。
7. **依赖**：公网发布前确认生产依赖审计为 0；当前已满足。

> 这些是部署配置项，不是代码功能缺失；按 `docs/DEPLOYMENT.md` 与 `docs/OPERATIONS.md` 执行即可。

---

## 5. 已知限制（不阻塞 MVP）

- 已支持账号删除；邮箱验证、找回密码、密码修改已支持。
- 无第三方登录（Provider 抽象已预留）。
- 无 OJ 提交同步的完整多平台支持；已支持 Codeforces 手动同步。
- 无提醒/通知；已支持 JSON 数据导出。
- 单实例部署；多实例需独立迁移 Job 与共享 Redis/DB。
- Monaco 编码页 chunk 仍约 2.7MB，仅在编码任务异步加载；Analytics 已按需引入 ECharts。
- 登录限流在 Redis 故障时 fail-open。
- Vitest 3 dev 依赖有审计告警，生产包不受影响。
- Playwright E2E 已纳入 CI。

---

## 6. 结论

- **代码与功能：MVP 验收通过。**
- **本地生产 Compose：部署、健康检查、备份恢复、CSP 下页面验证通过。**
- **公网发布：有条件可发布**，需先完成第 4 节 7 个部署前置项。
- 发布后按 `docs/MVP_RELEASE_REPORT.md` 的监控与下一版建议执行。
