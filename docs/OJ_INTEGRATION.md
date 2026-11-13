# MomoCode OJ 集成说明（Codeforces 手动同步）

| 项 | 内容 |
|---|---|
| 版本 | v1.1 |
| 日期 | 2026-11-11 |
| 范围 | 手动关联 + Codeforces 手动同步 |
| 官方接口 | `GET https://codeforces.com/api/user.status` |
| 触发方式 | 用户在 Settings 中手动点击“同步” |

---

## 1. 设计原则

- **不保存 OJ 密码**：只保存公开 handle。
- **手动触发**：不做后台自动轮询，避免违反平台频率限制与隐私预期。
- **只读**：只读取公开提交，不提交、不改动 OJ 数据。
- **失败不破坏本地数据**：同步失败不删除已有 Submission 或训练 Session。
- **可幂等**：以 `(user_id, platform, external_id)` 去重，重复同步不产生重复记录。
- **内置判题与 OJ 证据分离**：内置测试用例判题负责即时反馈；同步的 verdict 是独立 OJ 证据，不替代内置判题或 Skill Score。

---

## 2. Codeforces API 契约

官方方法：

```text
GET https://codeforces.com/api/user.status?handle=<handle>&from=1&count=100
```

- 公开只读，匿名可访问。
- 返回 `{"status":"OK","result":[Submission...]}`；失败时 `status!="OK"`。
- Submission 关键字段：
  - `id` → 本地 `external_id`
  - `creationTimeSeconds` → `submitted_at`（UTC）
  - `problem.contestId` + `problem.index` → `problem_ref`、题目 URL
  - `verdict` → 归一化 verdict，原值保存到 `verdict_raw`
  - `programmingLanguage` → `language`
  - `timeConsumedMillis` → `time_ms`
  - `memoryConsumedBytes` → `memory_kb`（字节 / 1024）
- 官方文档：
  - https://codeforces.com/apiHelp/methods
  - https://codeforces.com/apiHelp/objects

---

## 3. Verdict 映射

| Codeforces | MomoCode |
|---|---|
| `OK` | `accepted` |
| `WRONG_ANSWER` | `wrong_answer` |
| `TIME_LIMIT_EXCEEDED` | `time_limit_exceeded` |
| `MEMORY_LIMIT_EXCEEDED` | `memory_limit_exceeded` |
| `RUNTIME_ERROR` | `runtime_error` |
| `COMPILATION_ERROR` | `compilation_error` |
| `PARTIAL` | `partially_accepted` |
| 其他/缺失 | `other` / `null` |

原始值始终保存在 `verdict_raw`，不丢信息。

---

## 4. 同步流程

1. 用户在 Settings 添加 Codeforces handle。
2. 点击“同步”。
3. 后端校验账号归属与平台（仅 Codeforces）。
4. Redis 限流：每用户 5 次 / 5 分钟。
5. Adapter 调用官方 API，15 秒超时，网络/5xx 最多重试 3 次。
6. 归一化 Submission，按 `(user_id, platform, external_id)` 跳过已存在记录。
7. 新记录写入 `submissions`，`source='oj_sync'`，关联 `oj_account_id`。
8. 更新 `oj_accounts.last_synced_at`。
9. 返回 `fetched / created / skipped / last_synced_at`。

同步不会自动关联训练 Session；用户仍需在结果页手动关联，以保持证据链可控。

---

## 5. 错误与边界

| 情况 | 行为 |
|---|---|
| 网络超时/5xx | 重试 3 次；仍失败返回 502 `OJ_SYNC_FAILED`，本地数据不变 |
| Codeforces 返回 FAILED | 502 `OJ_SYNC_FAILED` |
| 非 Codeforces 账号 | 422 `OJ_SYNC_UNSUPPORTED` |
| 账号不属于当前用户 | 404 `OJ_ACCOUNT_NOT_FOUND` |
| 同步并发/唯一键冲突 | 409 `OJ_SYNC_CONFLICT`，可重试 |
| 重复同步 | 200，`created=0`，`skipped>0` |
| 缺少 contestId（部分 gym/自定义题） | `problem_ref` 退化为 index；题目 URL 为 null |
| 无 verdict | `verdict=null`，保留原始缺失状态 |

---

## 6. 频率与合规

- 仅用户手动触发，单次最多拉取 100 条。
- 应用内限流 5 次 / 5 分钟 / 用户。
- 不抓取源代码，不模拟登录，不绕过平台限制。
- 遵守 Codeforces API 使用条款与合理频率；如平台返回限流/失败，直接向用户报错。
- 后续如需增量同步，应增加游标/最后提交 ID，而不是频繁全量拉取。

---

## 7. 验证与限制

已实现：

- `CodeforcesAdapter` 归一化与重试。
- 同步 API、幂等去重、失败回滚、平台/归属校验。
- 前端 Settings 手动同步按钮与结果提示。
- 后端测试使用 mock Adapter，不依赖真实网络：
  - 正常同步、重复同步、非 Codeforces、失败不写入、跨用户拒绝。
- 实时验证（2026-11-11）：
  - Adapter 直接调用 `user.status` 成功，读取 `tourist` 最近 1 条提交，归一化为 `accepted`。
  - 完整 API 同步使用 `tourist`：首次 `fetched=100, created=100, skipped=0`；第二次 `created=0, skipped=100`。
  - 验证后删除测试用户及其级联数据。

未验证/限制：

- CI 不调用真实 Codeforces API（避免外部依赖与频率问题）；本次为手动实时验证。
- 仅拉取最近 100 条；尚无增量游标。
- 仅 Codeforces；洛谷、AtCoder 需要各自官方契约与合规评估。
- OJ submission 不会自动变成 Skill Score；仍需 Session 关联与内置判题。
