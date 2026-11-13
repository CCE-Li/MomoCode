# MomoCode 邮箱验证与密码重置

| 项 | 内容 |
|---|---|
| 版本 | v1.0 |
| 日期 | 2026-11-11 |
| 范围 | 邮箱验证、找回密码、SMTP/控制台邮件后端 |
| 存储 | `email_tokens`（仅存 token 哈希） |

---

## 1. 流程

### 邮箱验证

1. 注册成功后自动发送验证邮件。
2. 邮件链接：`{APP_BASE_URL}/verify-email?token=...`。
3. 前端调用 `POST /api/v1/auth/verify-email`。
4. 后端校验 token、用途、有效期与未使用状态，写入 `users.email_verified_at`。
5. token 标记已使用，不可复用。

### 找回密码

1. 用户在 `/forgot-password` 输入邮箱。
2. `POST /api/v1/auth/password-reset/request` 始终返回 202 与通用提示，避免邮箱枚举。
3. 若账号存在，发送 `{APP_BASE_URL}/reset-password?token=...`。
4. 前端调用 `POST /api/v1/auth/password-reset/confirm`。
5. 后端更新密码、标记 token 已用、撤销该用户所有会话。
6. 用户使用新密码重新登录。

---

## 2. 令牌安全

- 原始 token 只出现在邮件链接中；数据库只保存 SHA-256 哈希。
- 验证邮箱 token 有效期 24 小时。
- 重置密码 token 有效期 1 小时。
- 同一用户 + 用途只保留一个未使用 token；新 token 会作废旧 token。
- 使用后 `used_at` 写入，重复使用返回 400 `EMAIL_TOKEN_INVALID`。
- 重置密码撤销全部会话，包括当前会话。
- 不记录 token 到普通日志；控制台邮件后端仅在开发环境打印邮件内容。

---

## 3. 邮件后端

| `EMAIL_BACKEND` | 用途 |
|---|---|
| `console` | 开发默认；邮件内容写入应用日志，不真正发送 |
| `smtp` | 生产；通过 SMTP 发送纯文本邮件 |

SMTP 配置：

```text
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=...
SMTP_PASSWORD=...
SMTP_FROM=no-reply@example.com
SMTP_USE_TLS=true
```

生产环境启动校验：

- 必须 `EMAIL_BACKEND=smtp`。
- 必须配置 `SMTP_HOST`。
- 必须配置 `SESSION_SECRET` 与 `SESSION_COOKIE_SECURE=true`。

SMTP 临时失败不会导致注册失败；用户可在 Settings 重新发送验证邮件。密码重置请求同理，不会暴露发送失败细节。

---

## 4. API

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/api/v1/auth/verify-email` | 否 | token 验证邮箱 |
| POST | `/api/v1/auth/verify-email/resend` | 是 + CSRF | 重新发送验证邮件，3 次/小时 |
| POST | `/api/v1/auth/password-reset/request` | 否 | 请求重置，5 次/小时 |
| POST | `/api/v1/auth/password-reset/confirm` | 否 | 用 token 设置新密码 |

限流在 Redis 不可用时 fail-open，并记录 warning。

---

## 5. 前端

- `/verify-email`：读取 token，显示成功/失败；成功后刷新用户状态。
- `/forgot-password`：输入邮箱；始终显示通用提示。
- `/reset-password`：设置新密码；成功后提示所有设备已退出。
- 登录页提供“忘记密码”入口。
- AppShell 在邮箱未验证时显示提示条。
- Settings 显示“邮箱已验证/未验证”，未验证可重新发送。

---

## 6. 测试与验证

后端 `tests/test_email_auth.py` 覆盖：

- 注册发送验证邮件、token 验证成功、重复使用失败。
- 已验证用户重新发送不重复发送。
- 重置密码撤销全部会话、旧密码失效、新密码可登录。
- 未知邮箱返回通用 202，不发送邮件。
- 过期 token 返回 400。

浏览器验证：

- 注册后出现“邮箱未验证”提示。
- 验证链接成功；提示消失。
- 忘记密码页面返回通用提示。
- 重置密码成功后所有会话退出；新密码登录成功。

---

## 7. 已知限制

- 邮箱验证不阻塞登录；未验证用户仍可训练。
- 无邮件模板/多语言；当前为纯文本。
- SMTP 发送为同步调用放入线程池，未接队列；高并发时应改为异步邮件队列。
- 控制台邮件后端仅开发使用；生产启动校验会拒绝。
