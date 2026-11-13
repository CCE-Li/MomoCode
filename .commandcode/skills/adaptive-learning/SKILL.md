---
name: adaptive-learning
description: 负责个性化训练计划、难度动态调整与学习任务调度。当需要设计自适应学习策略、根据用户表现调整难度、安排学习任务或规划学习路径时使用。
---

# Adaptive Learning

决策层：依据用户状态，决定“学什么、多难、何时练”，并排布学习任务。

## 职责范围

- 个性化训练计划。
- 难度动态调整。
- 学习任务调度与学习路径规划。

## 触发时机

- 设计自适应学习策略。
- 根据用户表现调整难度。
- 安排学习任务或规划学习路径。

## 工作流程

1. 读取用户状态：掌握度（来自 `spaced-repetition`）与表现指标（来自 `coding-performance`）。
2. 依据规则选择训练内容与训练形式（形式来自 `code-template-training`）。
3. 调整难度。
4. 排布任务队列与学习路径。
5. 记录每次决策的依据，便于回溯。

## 边界与禁止

- 只做“学什么 / 多难 / 何时练”的决策。
- 消费 `coding-performance` 的指标与 `spaced-repetition` 的复习状态，不重复实现它们。
- 训练形式与判定 → `code-template-training`；表现指标口径 → `coding-performance`；知识结构 → `algorithm-taxonomy`。
- 不臆造未确认的调度依据或外部能力。

## 输出物

- 调度策略。
- 难度调整规则。
- 训练计划结构。

## 反虚构约定

外部 OJ、平台或库的真实字段、端点、参数在无确认来源前一律不写死；不确定处标注 `TODO(确认来源)`。

## references 使用

当调度策略的描述较长时，放入本 Skill 的 `references/`（如 `references/scheduling-policy.md`），并在正文用相对路径引用。
