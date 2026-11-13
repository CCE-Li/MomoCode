# MomoCode 算法知识库与内容规范（阶段 8）

| 项 | 内容 |
|---|---|
| 阶段 | 阶段 8：算法知识库与内容 |
| 版本 | v1.0 |
| 状态 | 种子内容已入库验证 |
| 依据 | `docs/PRD.md`、`docs/DATABASE.md`、`docs/ARCHITECTURE.md` |
| 种子目录 | `content/seed/v2/`（`v1` 为历史与测试基线） |
| 导入脚本 | `backend/scripts/seed_content.py` |
| 生成脚本 | `backend/scripts/build_manual_seed.py` |
| 日期 | 2026-11-10（2026-11-11 更新 v2） |

> 2026-11-11 更新：生产种子已切换到 `content/seed/v2/`，包含 7 个分类、37 个算法、94 个技能、200 个训练任务，其中 106 个为 `oj_reference` 模板题任务。下文关于 v1 初始规模的描述保留为阶段 8 历史记录；当前规模以 v2 manifest 为准。

---

## 1. 目标与范围

本阶段建立可维护的算法内容体系：

- 当前 v2：7 个分类、37 个算法、94 个技能、200 个训练任务，其中 106 个为 `oj_reference`。
- v1 历史基线：3 个分类、10 个算法、40 个技能、40 个原创任务，每算法覆盖四类训练。
- 内容版本、校验和与幂等导入机制。
- 不实现训练会话、FSRS、OJ 或 Analytics 业务（阶段 9+）。

---

## 2. 内容原则

1. **任务必须训练明确技能**：每个 `PracticeTask` 至少关联一个 `target` 技能。
2. **Algorithm、Skill、Task 不合并**：算法是知识单元，技能是训练能力单元，任务是具体练习。
3. **不编造 OJ 题目**：v1 任务全部为原创内容；v2 新增的 `oj_reference` 任务必须记录真实平台、题号与 URL，不复制受限题面，`source_type='oj_reference'`。
4. **复习默认隐藏答案**：`reference_solution_md` 在训练时不可见，只在结果页显式展开。
5. **复杂算法拆独立技能**：识别、基础实现、变体、常见错误分别成技能，不混在一个技能里。
6. **一次 AC 不等于掌握**：任务只提供证据，掌握状态由后续 FSRS/证据评估决定。
7. **内容可追溯**：种子版本、校验和、导入时间与操作者写入 `content_versions`。
8. **许可清晰**：原创内容可维护；引用 OJ 题目时必须记录来源并遵守平台条款，不复制受限题面。

---

## 3. 实体与字段规范

### 3.1 AlgorithmCategory

| 字段 | 规范 |
|---|---|
| `slug` | 小写 kebab-case，全局唯一，如 `basics`。 |
| `name` | 中文展示名，如“基础算法”。 |
| `description` | 分类说明，可为空。 |
| `sort_order` | 数字越小越靠前。 |
| `is_active` | 软删除标记；内容下架用 false，不物理删除。 |

### 3.2 Algorithm

| 字段 | 规范 |
|---|---|
| `slug` | 小写 kebab-case，全局唯一，如 `binary-search`。 |
| `category_slug` | 必须引用已存在的分类。 |
| `name` | 中文算法名。 |
| `summary` | 一句话摘要，列表页使用。 |
| `description_md` | Markdown 详情。 |
| `difficulty` | 1–5，表示学习难度，不是用户能力。 |
| `prerequisites` | 字符串数组，前置知识/技能提示。 |
| `is_active` | 软删除标记。 |

### 3.3 Skill

| 字段 | 规范 |
|---|---|
| `slug` | `<algorithm>-<type>`，如 `binary-search-template`；全局唯一。 |
| `algorithm_slug` | 必须引用已存在的算法。 |
| `name` | 中文技能名。 |
| `skill_type` | `recognition`、`base_implementation`、`variant`、`common_error` 四选一。 |
| `description_md` | 技能说明。 |
| `learning_objective` | 学习目标。 |
| `mastery_evidence_md` | 什么证据算掌握；不能写成“一次 AC 即掌握”。 |
| `common_mistakes_md` | 易错点。 |
| `prerequisites` | 字符串数组。 |
| `sort_order` | 同一算法内的展示顺序。 |
| `is_active` | 软删除标记。 |

### 3.4 PracticeTask

| 字段 | 规范 |
|---|---|
| `slug` | 全局唯一，如 `binary-search-template-001`。 |
| `title` | 中文任务标题。 |
| `training_type` | `recognition`、`template`、`variant`、`correction`。 |
| `evaluation_mode` | 识别任务 `auto_recognition`；编码任务 `auto_tests`。 |
| `difficulty` | 1–5。 |
| `source_type` | `original`、`oj_reference`、`user`。 |
| `source_ref` | OJ 引用说明；原创任务为 null。 |
| `oj_platform` / `oj_problem_ref` / `oj_problem_url` | 三者要么为空，要么由合法来源填写；MVP 种子全部为 null。 |
| `statement_md` | 题面/任务说明。 |
| `constraints_md` | 数据范围与约束。 |
| `input_spec` | 作答输入结构说明（JSON）。 |
| `expected_output_spec` | 期望输出/判定说明（JSON）。 |
| `code_scaffold` | 起始代码；纠错任务放缺陷代码。 |
| `reference_solution_md` | 参考实现；训练时隐藏。 |
| `language` | MVP 为 `cpp17`。 |
| `hints` | 键为 `"1"`–`"5"` 的提示内容。 |
| `max_hint_level` | 识别任务 ≤3；编码任务可为 5。 |
| `error_types` | 纠错任务预设错误类型数组。 |
| `is_active` | 软删除标记。 |

### 3.5 TaskSkill

| 字段 | 规范 |
|---|---|
| `task_id` + `skill_id` | 复合主键。 |
| `relation_type` | `target`（判分/训练目标）或 `related`（相关技能）。 |
| `is_primary` | 每个任务最多一个主技能；第一个 target 默认 primary。 |

规则：

- 每个任务至少一个 `target`。
- `target` 与 `related` 不重叠。
- 识别任务的 `target` 技能集合就是自动判分答案。
- 编码任务通常一个 `target`，可有多个 `related`。

### 3.6 ContentVersion

| 字段 | 规范 |
|---|---|
| `version` | 内容版本，如 `2026.11.2`。 |
| `checksum` | 所有种子文件内容 + 文件名的 SHA-256。 |
| `notes` | 变更说明。 |
| `applied_at` | 导入时间（UTC）。 |
| `applied_by` | 导入脚本/操作者。 |

---

## 4. 技能拆分规范

每个算法固定拆为四类技能：

| 类型 | 目的 | 典型任务 |
|---|---|---|
| `recognition` | 看题判断是否/如何用该算法 | 选择题、算法匹配 |
| `base_implementation` | 不看参考代码写出基础模板 | 模板复现 |
| `variant` | 掌握算法变化与迁移 | 变体复现 |
| `common_error` | 定位并修复典型错误 | 针对性纠错 |

命名：

- slug：`<algorithm>-<type>`，例如 `bfs-template`。
- 中文名：动词开头，明确训练对象，例如“独立复现队列 BFS 模板”。
- 掌握证据必须可观察：正确性、独立程度、提示等级、OJ 证据，禁止只写“理解了”。

---

## 5. 难度与提示等级

### 5.1 难度

| 等级 | 含义 |
|---|---|
| 1 | 入门，单一模板或直接识别。 |
| 2 | 基础应用，需要边界或结构变化。 |
| 3 | 需要组合知识或较复杂的变体。 |
| 4 | 多步推理、复杂状态或路径恢复。 |
| 5 | 高难综合；MVP 种子暂不大量覆盖。 |

难度用于内容排序与耗时归一化，不是用户能力分数。

### 5.2 提示等级

| 等级 | 内容 | 识别任务 | 编码任务 |
|---|---|---|---|
| 0 | 无提示 | 是 | 是 |
| 1 | 算法类别 | 是 | 是 |
| 2 | 核心思想 | 是 | 是 |
| 3 | 数据结构/状态 | 是 | 是 |
| 4 | 部分代码 | 否 | 是 |
| 5 | 完整参考实现 | 否 | 是 |

识别任务 `max_hint_level=3`；编码任务 `max_hint_level=5`。提示使用必须记录，影响独立程度证据，不直接等于遗忘。

---

## 6. 评测与证据

| 训练类型 | 正确性来源 | 说明 |
|---|---|---|
| 识别 | 系统自动判分 | 与 `target` 技能集合比对；完全匹配/部分匹配/错误。 |
| 模板 | 内置测试自动判题 + 可选 OJ 关联 | Docker 容器编译运行；OJ Verdict 是独立证据。 |
| 变体 | 内置测试自动判题 + 可选 OJ 关联 | 额外记录变体表现。 |
| 纠错 | 内置测试自动判题 + 可选 OJ 关联 | 使用对应模板的 main 包装后判题，并记录错误类型。 |

禁止：

- 把 OJ AC 自动写成“已掌握”。
- 把内置判题结果与 OJ 证据相互覆盖。
- 在识别任务中提供第 4/5 级提示。

---

## 7. 任务 Schema 示例

```json
{
  "slug": "binary-search-recognition-001",
  "title": "识别：有序数组查找目标值",
  "training_type": "recognition",
  "evaluation_mode": "auto_recognition",
  "difficulty": 1,
  "source_type": "original",
  "source_ref": null,
  "oj_platform": null,
  "oj_problem_ref": null,
  "oj_problem_url": null,
  "statement_md": "给定升序数组与目标值，判断目标值是否存在。请选择最合适的算法/技能。",
  "constraints_md": "1 ≤ n ≤ 100000；数组严格升序。",
  "input_spec": {"answer": "selected_skill_ids", "multi_select": false},
  "expected_output_spec": {"target_skills": ["binary-search-recognition"]},
  "code_scaffold": null,
  "reference_solution_md": null,
  "language": "cpp17",
  "hints": {
    "1": "考虑有序性带来的搜索空间缩减。",
    "2": "每次比较中间元素可以排除一半区间。",
    "3": "维护左右边界，注意区间开闭与终止条件。"
  },
  "max_hint_level": 3,
  "error_types": [],
  "target_skills": ["binary-search-recognition"],
  "related_skills": ["binary-search-template"]
}
```

校验规则由 `backend/scripts/seed_content.py` 的 Pydantic 模型执行：

- 分类/算法/技能引用必须存在。
- slug 不重复。
- target/related 技能不重叠、不未知。
- 识别任务只能自动判分且提示 ≤3。
- 编码任务必须使用 `auto_tests` 且提示 ≤5。
- `auto_tests` 的 `expected_output_spec.judge.test_cases` 至少有一个 `{input, output}`。
- 纠错任务额外提供 `judge.harness_main`（对应模板的 main），用于包装函数级代码。
- `hints` 键必须在 `1..max_hint_level` 内。
- OJ 平台与题目引用必须同时为空或同时存在。

### 7.1 自动判题配置

```json
{
  "evaluation_mode": "auto_tests",
  "expected_output_spec": {
    "evaluation": "auto_tests",
    "judge": {
      "test_cases": [
        {"input": "5 4\n1 3 5 7 9\n1 5 10 3\n", "output": "0\n2\n5\n1\n"}
      ],
      "harness_main": "int main() { ... }"
    }
  }
}
```

- 模板/变体任务的用户代码必须自带 `main`，`harness_main` 可省略。
- 纠错任务通常是函数级代码，`harness_main` 提供对应模板的 `main`；判题器会拼接 `#include <bits/stdc++.h>`、用户代码和 harness。
- 判题容器限制：禁网、只读根文件系统、非 root、CPU/内存/进程数/时间限制。

---

## 8. 种子数据布局与版本管理

```text
content/seed/v2/          # 当前生产内容
├── manifest.json       # version、description、files
├── categories.json     # 7 个分类
├── algorithms.json     # 37 个算法
├── skills.json         # 94 个技能
└── tasks.json          # 200 个任务（含 106 个 oj_reference）

content/seed/v1/          # 历史与测试基线，不再作为生产默认
```

- Task 可选 `tags: string[]`；v2 生成器按目标技能自动生成算法标签（如 `二分`、`双指针`、`BFS`），导入时写入 `task_tags`。
- `manifest.json` 的 `version` 唯一。
- 导入脚本对 `version + files` 计算 SHA-256，写入 `content_versions.checksum`。
- 同一版本且 checksum 相同：默认跳过，输出“already applied”。
- `--force`：重新 upsert 内容并刷新 checksum。
- 内容更新新增版本号（如 `2026.12.1`），不修改已应用版本的历史记录。
- 导入按 slug upsert，不物理删除；下架内容通过 `is_active=false`（当前脚本只 upsert，不自动下架）。
- 任务技能关联每次导入先删除该任务的关联，再按种子重建，保证 `target/related` 与主技能一致。

### 导入命令

```powershell
docker compose up -d --wait
cd backend
uv run alembic upgrade head
# 如修改了手册或章节映射，先重建 v2 JSON
uv run python -m scripts.build_manual_seed
uv run python -m scripts.seed_content
# 强制重放
uv run python -m scripts.seed_content --force
```

---

## 9. 初始算法清单

| 分类 | 算法 slug | 名称 | 难度 | 技能数 |
|---|---|---|---|---|
| 基础算法 | `binary-search` | 二分查找 | 1 | 4 |
| 基础算法 | `two-pointers` | 双指针 | 2 | 4 |
| 基础算法 | `prefix-sum` | 前缀和 | 1 | 4 |
| 基础算法 | `difference-array` | 差分 | 2 | 4 |
| 图论与搜索 | `bfs` | BFS | 2 | 4 |
| 图论与搜索 | `dfs` | DFS | 2 | 4 |
| 图论与搜索 | `dijkstra` | Dijkstra | 3 | 4 |
| 图论与搜索 | `union-find` | 并查集 | 3 | 4 |
| 动态规划 | `knapsack-01` | 01 背包 | 3 | 4 |
| 动态规划 | `lis` | 最长上升子序列（LIS） | 3 | 4 |

---

## 10. 技能清单（40）

| 算法 | 技能 slug | 名称 | 类型 |
|---|---|---|---|
| binary-search | `binary-search-recognition` | 识别二分查找适用场景 | recognition |
| binary-search | `binary-search-template` | 独立复现二分模板 | base_implementation |
| binary-search | `binary-search-variant` | 二分答案与边界变体 | variant |
| binary-search | `binary-search-errors` | 二分边界与死循环纠错 | common_error |
| two-pointers | `two-pointers-recognition` | 识别双指针适用场景 | recognition |
| two-pointers | `two-pointers-template` | 独立复现对撞双指针模板 | base_implementation |
| two-pointers | `two-pointers-variant` | 快慢指针与区间收缩变体 | variant |
| two-pointers | `two-pointers-errors` | 指针移动与去重纠错 | common_error |
| prefix-sum | `prefix-sum-recognition` | 识别前缀和适用场景 | recognition |
| prefix-sum | `prefix-sum-template` | 独立复现一维前缀和模板 | base_implementation |
| prefix-sum | `prefix-sum-variant` | 二维前缀和与哈希变体 | variant |
| prefix-sum | `prefix-sum-errors` | 下标与前缀初始化纠错 | common_error |
| difference-array | `difference-array-recognition` | 识别差分适用场景 | recognition |
| difference-array | `difference-array-template` | 独立复现一维差分模板 | base_implementation |
| difference-array | `difference-array-variant` | 二维差分与区间修改变体 | variant |
| difference-array | `difference-array-errors` | 差分边界与还原纠错 | common_error |
| bfs | `bfs-recognition` | 识别 BFS 适用场景 | recognition |
| bfs | `bfs-template` | 独立复现队列 BFS 模板 | base_implementation |
| bfs | `bfs-variant` | 多源 BFS 与路径恢复变体 | variant |
| bfs | `bfs-errors` | visited 时机与层数纠错 | common_error |
| dfs | `dfs-recognition` | 识别 DFS 适用场景 | recognition |
| dfs | `dfs-template` | 独立复现递归 DFS 模板 | base_implementation |
| dfs | `dfs-variant` | 连通块、记忆化与剪枝变体 | variant |
| dfs | `dfs-errors` | 递归边界与回溯纠错 | common_error |
| dijkstra | `dijkstra-recognition` | 识别 Dijkstra 适用场景 | recognition |
| dijkstra | `dijkstra-template` | 独立复现优先队列 Dijkstra 模板 | base_implementation |
| dijkstra | `dijkstra-variant` | 多源、路径恢复与次短路变体 | variant |
| dijkstra | `dijkstra-errors` | 松弛与堆过期纠错 | common_error |
| union-find | `union-find-recognition` | 识别并查集适用场景 | recognition |
| union-find | `union-find-template` | 独立复现路径压缩并查集模板 | base_implementation |
| union-find | `union-find-variant` | 带权并查集与连通块计数变体 | variant |
| union-find | `union-find-errors` | find 递归与合并纠错 | common_error |
| knapsack-01 | `knapsack-01-recognition` | 识别 01 背包适用场景 | recognition |
| knapsack-01 | `knapsack-01-template` | 独立复现一维 01 背包模板 | base_implementation |
| knapsack-01 | `knapsack-01-variant` | 恰好装满、方案数与路径恢复变体 | variant |
| knapsack-01 | `knapsack-01-errors` | 容量循环方向纠错 | common_error |
| lis | `lis-recognition` | 识别 LIS 适用场景 | recognition |
| lis | `lis-template` | 独立复现 O(n^2) LIS 模板 | base_implementation |
| lis | `lis-variant` | O(n log n) 二分与路径恢复变体 | variant |
| lis | `lis-errors` | 状态定义与二分替换纠错 | common_error |

---

## 11. 任务清单（19）

| 任务 slug | 训练类型 | 目标技能 | 难度 | 说明 |
|---|---|---|---|---|
| `binary-search-recognition-001` | recognition | binary-search-recognition | 1 | 有序数组查找目标值 |
| `binary-search-template-001` | template | binary-search-template | 1 | 实现 lower_bound |
| `binary-search-variant-001` | variant | binary-search-variant | 2 | 切割木头的最大长度 |
| `binary-search-errors-001` | correction | binary-search-errors | 2 | 二分死循环与溢出 |
| `two-pointers-recognition-001` | recognition | two-pointers-recognition | 2 | 有序数组两数之和 |
| `prefix-sum-recognition-001` | recognition | prefix-sum-recognition | 1 | 多次区间和查询 |
| `difference-array-recognition-001` | recognition | difference-array-recognition | 2 | 多次区间加一 |
| `bfs-recognition-001` | recognition | bfs-recognition | 2 | 网格最短步数 |
| `bfs-template-001` | template | bfs-template | 2 | 网格 BFS 最短步数 |
| `bfs-variant-001` | variant | bfs-variant | 3 | 01 矩阵到最近 0 |
| `bfs-errors-001` | correction | bfs-errors | 3 | 重复入队与层数错误 |
| `dfs-recognition-001` | recognition | dfs-recognition | 2 | 有向图环检测 |
| `dijkstra-recognition-001` | recognition | dijkstra-recognition | 3 | 非负权单源最短路 |
| `union-find-recognition-001` | recognition | union-find-recognition | 3 | 动态连通性查询 |
| `knapsack-01-recognition-001` | recognition | knapsack-01-recognition | 3 | 每件物品最多选一次 |
| `knapsack-01-template-001` | template | knapsack-01-template | 3 | 一维 01 背包 |
| `knapsack-01-variant-001` | variant | knapsack-01-variant | 4 | 恰好装满容量 |
| `knapsack-01-errors-001` | correction | knapsack-01-errors | 3 | 容量循环方向 |
| `lis-recognition-001` | recognition | lis-recognition | 3 | 最长严格上升子序列 |

代表性完整样例：

- **基础算法**：二分查找（识别、模板、变体、纠错）。
- **图论与搜索**：BFS（识别、模板、变体、纠错）。
- **动态规划**：01 背包（识别、模板、变体、纠错）。

---

## 12. 内容质量检查清单

- [ ] slug 全局唯一且符合命名规范。
- [ ] 算法有分类、难度、摘要。
- [ ] 每个算法 4 类技能齐全。
- [ ] 技能有学习目标、掌握证据、常见错误。
- [ ] 任务至少一个 target 技能。
- [ ] 识别任务 `auto_recognition` 且 `max_hint_level <= 3`。
- [ ] 编码任务 `auto_tests`、判题测试用例完整且提示内容完整。
- [ ] 纠错任务有 `code_scaffold` 和 `error_types`。
- [ ] 参考实现存在但训练时隐藏。
- [ ] 没有虚构 OJ ID/URL；原创任务 `source_type='original'`。
- [ ] `content_versions` 写入版本与 checksum。
- [ ] 重复导入幂等；`--force` 可重放。

---

## 13. 许可与来源

- v1 种子内容为项目原创；v2 新增 OJ 引用任务，未复制受限题面。
- 引用 OJ 题目时：
  - 记录 `source_type='oj_reference'`、`source_ref`、`oj_platform`、`oj_problem_ref`、`oj_problem_url`。
  - 遵守目标平台条款与许可；不抓取受限数据。
  - 题面以引用/摘要为主，不整段复制受版权保护内容。
- 用户自定义复习内容为私有 UGC（`user_review_items`），只对本人可见，不进入公共题库。
- 用户自建题目写入 `practice_tasks`（`source_type='user'`、`created_by_user_id`），只对本人可见；公共目录默认过滤，导入字段遵循本文的 Task 规范。

---

## 14. 待确认事项

1. **Q10 技能粒度**：当前每算法 4 类技能；是否需要为复杂算法增加更多变体/错误技能。
2. **任务数量**：当前 200 个任务（含 106 个 OJ 引用）；后续继续增加变体与错误样例。
3. **语言范围**：MVP 只承诺 C++17；是否在后续加入 Python/Java 模板。
4. **内容作者流程**：是否引入内容审核、草稿/发布状态与版本回滚。
5. **OJ 引用规范**：已记录 Codeforces/洛谷题号与 URL；后续补充 AtCoder 与平台许可复核。
6. **难度标定**：当前难度为内容作者估计；是否用用户表现数据校准。
