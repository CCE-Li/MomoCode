# MomoCode Analytics 指标口径（阶段 12）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 12：学习分析与 Dashboard |
| 版本 | v1.0 |
| 状态 | API 与页面已实现并通过测试 |
| 依据 | `docs/PRD.md`、`docs/DATABASE.md`、`docs/ARCHITECTURE.md` |
| 日期 | 2026-11-10 |

> 原则：每个指标必须有定义、公式、来源与时间范围；样本不足必须标注；不使用假数据；Skill Score 与 FSRS Difficulty 严格分开。

---

## 1. 数据来源

| 数据 | 表/来源 | 用途 |
|---|---|---|
| 训练会话 | `practice_sessions` | 完成次数、正确率、提示、耗时、错误类型 |
| 提示记录 | `session_hints` | 提示等级使用与独立程度 |
| 正式复习 | `review_logs` | 复习次数、评级、复习历史 |
| FSRS 状态 | `skill_memories` | 今日到期、下次到期 |
| OJ 提交 | `submissions` | 客观证据与 OJ 置信度 |
| 技能统计 | `user_skill_stats` | Skill Score 持久化聚合（可重算） |

时间范围：接口 `days` 参数，支持 7/30/90 天（1–365）。日期边界按用户时区计算；未设置时默认 UTC。

---

## 2. 核心指标

### 2.1 完成训练数（sessions_completed）

- 公式：所选时间范围内 `status='completed'` 的 Session 数。
- 来源：`practice_sessions`。
- 范围：所选时间范围。
- 说明：自由练习与正式复习都计入；正式复习由 `review_logs` 单独统计。

### 2.2 正确率（correctness_rate）

- 公式：
  - 识别：`auto_grade.result` → correct=1，partial=0.5，incorrect=0。
  - 编码类：`auto_grade.result` → correct=1，partial=0.5，incorrect/compile_error/runtime_error/time_limit_exceeded=0。
  - 对有效样本取平均。
- 来源：`practice_sessions.auto_grade` / `self_assessment`（旧数据兼容）。
- 范围：所选时间范围。
- 说明：
  - 内置判题结果与 OJ 证据分开记录；OJ Verdict 不覆盖内置判题。
  - 一次 AC 不等于掌握。
  - 无有效结果的 Session 不计入分母。

### 2.3 独立完成比例（independent_rate）

- 公式：`max_hint_level <= 1` 的已完成 Session 数 / 已完成 Session 数。
- 来源：`practice_sessions.max_hint_level`。
- 范围：所选时间范围。
- 说明：提示等级 0–1 视为基本独立；2–5 级按依赖提示处理。

### 2.4 提示依赖（hint_dependency）

- 公式：平均 `max_hint_level` / 5。
- 来源：`practice_sessions.max_hint_level`。
- 范围：所选时间范围。
- 说明：0 表示无提示；1 表示最高提示。提示依赖不是遗忘概率。

### 2.5 归一化耗时（avg_normalized_time）

- 公式：
  1. 对同一用户、同一 `training_type + difficulty` 的已完成 Session 求个人中位耗时。
  2. 每个 Session 的相对耗时 = 实际耗时 / 个人中位耗时。
  3. 对相对耗时取平均。
- 来源：`practice_sessions.time_spent_ms`、`training_type`、任务难度快照。
- 范围：所选时间范围。
- 说明：
  - 不跨算法做绝对耗时比较。
  - 缺少同组基准时返回 null，不用 0 或假数据填充。

### 2.6 今日到期（due_count）

- 公式：`skill_memories.due_at <= 用户时区今日结束时间`，且该技能有可用训练任务的数量。
- 来源：`skill_memories` + `task_skills`。
- 范围：今日（用户时区）。
- 说明：FSRS 只决定复习调度，不代表能力分数。

### 2.7 复习次数（reviewed_count）

- 公式：所选时间范围内 `review_logs` 数量。
- 来源：`review_logs`。
- 范围：所选时间范围。
- 说明：只有正式复习产生 ReviewLog；自由练习默认不产生。

### 2.8 训练类型分布

- 公式：按 `recognition / template / variant / correction` 分组统计 Session 数。
- 来源：`practice_sessions.training_type`。
- 范围：所选时间范围。
- 说明：四类训练分别展示，不合并成单一“刷题量”。

### 2.9 错误类型分布

- 公式：统计 Session `error_types` 中每个错误类型出现的次数。
- 来源：`practice_sessions.error_types`。
- 范围：所选时间范围。
- 说明：用于薄弱点训练；不同错误类型不可简单相加为“能力”。

### 2.10 遗忘曲线对比（forgetting_curve）

- Fibonacci 计划曲线：
  - 复习间隔：1、1、2、3、5、8、13、21 天；累计复习日为 1、2、4、7、12、20、33 天。
  - 两次复习之间使用指数遗忘：`R(t) = exp(-t / 1.5)`；每次复习时重置为 100%。
  - 用途：作为固定复习节奏的基准曲线，不代表用户真实记忆。
- 我的曲线：
  - 取当前用户所有 `skill_memories.stability` 的均值 `S`。
  - 使用 FSRS 遗忘公式：`R(t) = (1 + 0.980346 * t / S) ** -0.1542`。
  - 样本技能数 `<3` 时标记 `insufficient_data=true`，曲线仅作参考。
- 来源：`skill_memories.stability`；不把 OJ verdict 混入曲线。
- 范围：0–30 天（可通过 `horizon_days` 调整到 7–60）。
- 说明：两条曲线模型不同，只用于观察复习节奏与个人记忆衰减的差异，不做绝对能力比较。

---

## 3. Skill Score v0

### 3.1 公式

```
weighted =
  0.35 * correctness
+ 0.25 * independence
+ 0.15 * consistency
+ 0.15 * oj_confidence
+ 0.10 * variant_performance

skill_score = round(weighted * 100, 2)
```

| 分量 | 定义 |
|---|---|
| correctness | 该技能在时间范围内的平均正确率（自动判题 / 识别判分） |
| independence | `max_hint_level <= 1` 的 Session 比例 |
| consistency | 上半段与下半段正确率差异：`1 - abs(later - earlier)`；样本 <2 时为 0.5 |
| oj_confidence | 关联该技能 Session 的 OJ 提交中 `accepted` 比例；无 OJ 证据时 0.5 |
| variant_performance | 变体训练正确率；无变体记录时使用整体正确率 |

样本规则：

- `sample_size < 3`：`insufficient_data=true`，`skill_score=null`，界面显示“样本不足”。
- `3 <= sample_size < 10`：显示分数并标注“初步数据”。
- `sample_size >= 10`：正常显示。

### 3.2 明确禁止

- 不用 FSRS `difficulty` 或 `stability` 计算 Skill Score。
- 不用单次 AC 直接判定高 Skill Score。
- 不在图表中把 FSRS Difficulty 标注为“能力”。
- 不把不同算法的原始耗时直接横向比较。

### 3.3 持久化

- `user_skill_stats` 保存最近一次计算的聚合结果。
- 该表可重算，不是事实来源；事实来源仍是 Session/ReviewLog/Submission。
- 计算时机：调用 `GET /api/v1/analytics/skills` 时重算并 upsert。

---

## 4. API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/analytics/overview?days=30` | KPI、训练类型分布、今日到期、复习次数 |
| GET | `/api/v1/analytics/trends?days=30` | 每日正确率/独立比例趋势 |
| GET | `/api/v1/analytics/errors?days=30` | 错误类型分布 |
| GET | `/api/v1/analytics/skills?days=30` | 技能维度 Skill Score 与样本量 |
| GET | `/api/v1/analytics/definitions` | 指标定义、公式、来源、时间范围 |

所有分析接口要求登录；数据按当前用户隔离。

---

## 5. 页面展示

- 时间范围：7/30/90 天。
- KPI：完成训练、正确率、独立完成、提示依赖、归一化耗时、今日到期。
- 图表：
  - 正确率与独立比例趋势（折线）。
  - 训练类型分布（柱状）。
  - 错误类型分布（横向柱状）。
  - 复习状态（今日到期、已复习）。
- 技能表：Skill Score、样本量、正确率、独立比例、提示依赖。
- 指标定义区：从 API 获取，展示公式、来源、范围与注意事项。
- 样本不足：顶部提示 + 技能行“样本不足/初步数据”徽标。
- 无数据：明确空状态，不显示假数据。

---

## 6. 测试覆盖

后端 `tests/test_analytics.py` 覆盖：

- 5 个 Session 的完成数、正确率、独立比例、提示依赖。
- 归一化耗时范围校验。
- 30 天趋势点数与 Session 总数一致。
- 错误类型分布。
- Skill Score 样本 >=3 时非空，`score_version=skill-score-v0`。
- 样本 <3 时 `insufficient_data=true` 且 `skill_score=null`。
- 指标定义包含 7 个核心键。

前端通过类型检查、Lint、构建与浏览器验证（Analytics 页面、样本不足提示、指标定义）。

---

## 7. 已知限制

- 归一化耗时依赖个人历史基准；样本不足时返回 null。
- OJ 证据目前只来自手动关联；OJ 同步在后续版本。
- Skill Score 是 v0 产品规则，权重可迭代；调整时需更新 `score_version` 与测试。
- 时间范围按用户时区计算；用户偏好编辑接口尚未开放，默认 UTC。
- 数据量增大后，读时聚合需要物化视图/预聚合。
