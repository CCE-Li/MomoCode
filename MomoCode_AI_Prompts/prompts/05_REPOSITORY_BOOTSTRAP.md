# 阶段 5：仓库初始化

先检查现有仓库、Git 状态和已确认文档。

## 目标
搭建最小可运行骨架，不实现复杂业务。

## 工作
1. 检查目录、依赖和已有代码。
2. 决定 monorepo 或分目录方案并说明理由。
3. 初始化 Vue 3 + TypeScript + Vite。
4. 初始化 FastAPI。
5. 配置格式化、Lint、类型检查和环境变量模板。
6. 按需配置 Docker Compose。
7. 建立 README、本地开发说明、健康检查和基础 CI。

## 约束
不实现算法、FSRS、OJ 业务；不覆盖或删除用户代码；不提交真实密钥；依赖需检查兼容性。

## 输出
创建实际项目骨架，更新 README、`.env.example`、`.gitignore`、`docs/DEVELOPMENT.md`。

## 验收
前后端可启动、健康检查通过、Lint/类型检查/基础测试可运行，README 命令已实际验证。
