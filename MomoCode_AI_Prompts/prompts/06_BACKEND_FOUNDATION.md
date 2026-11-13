# 阶段 6：后端基础设施

先检查仓库、架构和数据库文档。

## 目标
建立稳定的 FastAPI 基础服务。

## 工作
配置应用入口、API 版本路由、Pydantic Settings、SQLAlchemy Session、PostgreSQL、Alembic、统一异常处理、日志、请求 ID、健康检查、认证基础框架和 pytest 测试结构。

## 约束
路由不承载业务逻辑；Session 不可作为全局共享对象；密钥不可硬编码；数据库结构变更必须有迁移。

## 验收
应用启动、数据库连接、Alembic 升级、健康检查和示例 API 测试通过。汇报文件、命令、迁移和测试结果。
