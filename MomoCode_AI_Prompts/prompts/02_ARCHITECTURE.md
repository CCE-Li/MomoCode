# 阶段 2：系统架构设计

先阅读项目上下文和已确认的 `docs/PRD.md`。PRD 缺失或未确认时先停止并说明。

## 目标
设计覆盖 MVP 的整体架构，明确模块边界和依赖方向。

## 工作
1. 定义前端、后端、数据库、缓存和后台任务职责。
2. 设计 Auth、Algorithm Catalog、Skill、Practice、Review/FSRS、OJ Integration、Analytics 模块。
3. 明确 FSRS Engine、Skill Engine、Task Engine 的输入输出。
4. 设计 OJ Adapter 抽象。
5. 设计 API 版本、认证、错误响应规范。
6. 划分同步请求和后台任务。
7. 设计日志、配置、异常处理和可观测性。
8. 评估架构复杂度与扩展成本。

## 约束
默认模块化单体，不无理由拆微服务；不开发判题服务器；FSRS 不依赖具体 OJ；前端不直连数据库；不擅自替换技术栈。说明选型理由、代价和替代方案。

## 输出
创建 `docs/ARCHITECTURE.md`，包含系统图、模块图（Mermaid）、职责与依赖、数据流、API 规范、安全边界、部署拓扑、ADR 和待确认事项。

## 完成标准
架构覆盖 PRD 的 MVP，避免循环依赖。列出待确认决策，不开始业务编码。
