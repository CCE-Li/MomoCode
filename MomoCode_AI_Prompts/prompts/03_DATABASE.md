# 阶段 3：数据库与领域模型

先阅读项目上下文、PRD 和架构文档；发现缺失或冲突先报告。

## 目标
设计可迁移、可约束、可查询的关系型数据模型。

## 必须评估的实体
User、OJAccount、AlgorithmCategory、Algorithm、Skill、PracticeTask、TaskSkillRelation、SkillMemory、PracticeSession、ReviewLog、Submission、UserSkillStats。

## 工作
1. 定义字段、类型、主外键、唯一约束。
2. Algorithm 与 Skill 一对多；Task 与 Skill 多对多。
3. SkillMemory 以 user_id + skill_id 唯一。
4. 设计 Session 与 Submission 关联。
5. 设计 ReviewLog 和 FSRS 状态持久化。
6. 统一 OJ 字段并允许平台缺失值。
7. 设计索引、级联删除、数据隔离和历史保留策略。
8. 区分实时计算、缓存和持久化统计。

## 约束
Skill Score 不得与 FSRS 参数混淆；Submission 不等于 Session；所有用户数据必须隔离；不要过度抽象；FSRS 字段以选定库的数据结构为准。

## 输出
创建 `docs/DATABASE.md`，包含 ER 图、数据字典、约束、索引、关键查询、迁移策略、示例数据和待确认事项。

## 完成标准
开发者可按文档创建数据库。此阶段只设计，不生成全量 ORM 代码。
