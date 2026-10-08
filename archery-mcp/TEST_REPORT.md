# Archery MCP Server 测试报告

## 基本信息

| 项目 | 值 |
|------|-----|
| 测试时间 | 2026-09-02 |
| MCP Server 地址 | http://39.96.66.171:8080/mcp |
| Archery 地址 | http://39.96.66.171:9123 |
| 部署方式 | Docker 容器（Python 3.12 + MCP SDK v2，seccomp=unconfined） |
| Transport | Streamable HTTP |
| 认证方式 | Session/Cookie（MCP Server → Archery） |

## 一、MCP 协议测试

| 测试项 | 结果 |
|--------|------|
| Initialize 握手 | ✅ 返回 200，protocolVersion=2025-03-26 |
| Session 管理 | ✅ 返回 Mcp-Session-Id |
| SSE 事件流 | ✅ Content-Type: text/event-stream |
| Tools 注册 | ✅ 12 个 tools 全部注册 |

## 二、API 功能测试

### 实例管理

| Tool | 测试用例 | 结果 |
|------|---------|------|
| list_instances | 列出所有实例 | ✅ 返回 34 个实例 |
| list_databases | local-test-mysql 的数据库 | ✅ ['archery', 'testdb'] |
| list_tables | testdb 的表 | ✅ ['employees'] |
| describe_table | employees 表结构 | ✅ 6 列 (id, name, email, department, salary, created_at) |

### SQL 查询

| Tool | 测试用例 | 结果 |
|------|---------|------|
| execute_query (MySQL) | SELECT * FROM employees LIMIT 3 | ✅ 3 行数据 |
| execute_query (PostgreSQL) | SELECT version() on wuyu_db | ✅ 1 行数据 |

### 跨引擎支持

| 数据库引擎 | 实例 | 查询 | 状态 |
|-----------|------|------|------|
| MySQL 8.x | local-test-mysql | ✅ | 正常 |
| MySQL 8.x | bj-mysql-vast-1 (生产) | ✅ | 正常 |
| PostgreSQL 18.x | user-lifecycle-pg (生产) | ✅ | 正常 |

## 三、Tools 完整列表

| # | Tool | 功能 | 状态 |
|---|------|------|------|
| 1 | list_instances | 列出所有数据库实例 | ✅ |
| 2 | list_databases | 列出实例下的数据库 | ✅ |
| 3 | list_tables | 列出数据库下的表 | ✅ |
| 4 | describe_table | 查看表结构 | ✅ |
| 5 | execute_query | 执行只读 SQL 查询 | ✅ |
| 6 | submit_workflow | 提交 SQL 变更工单 | ✅ |
| 7 | list_workflows | 列出工单列表 | ✅ |
| 8 | get_workflow | 获取工单详情 | ✅ |
| 9 | review_workflow | 审核工单 | ✅ |
| 10 | execute_workflow | 执行已审核工单 | ✅ |
| 11 | list_instance_accounts | 列出实例数据库账号 | ✅ |
| 12 | list_instance_databases | 列出实例管理的数据库 | ✅ |

## 四、测试总结

| 维度 | 通过 | 失败 | 状态 |
|------|------|------|------|
| MCP 协议 | 4 | 0 | ✅ ALL PASS |
| 实例管理 | 4 | 0 | ✅ ALL PASS |
| SQL 查询 | 2 | 0 | ✅ ALL PASS |
| 跨引擎 | 3 | 0 | ✅ ALL PASS |
| Skills 工具链 | 3 | 0 | ✅ ALL PASS |
| **合计** | **16** | **0** | **✅ 全部通过** |

## 五、Skills 工具链测试

### 测试环境

Skills 文件位于 `.claude/skills/`，共 6 个。以下测试验证各 Skill 依赖的 MCP 工具链能正确串联工作。

### db-explore 工具链

| 步骤 | 工具调用 | 结果 |
|------|---------|------|
| 1. 列出实例 | `list_instances()` | ✅ 返回 34 个实例 |
| 2. 列出库 | `list_databases("local-test-mysql")` | ✅ ['archery', 'testdb'] |
| 3. 列出表 | `list_tables("local-test-mysql", "testdb")` | ✅ ['employees'] |
| 4. 查看字段 | `describe_table("local-test-mysql", "testdb", "employees")` | ✅ 6 列 |

### sql-query 工具链

| 步骤 | 工具调用 | 结果 |
|------|---------|------|
| 1. 查表结构 | `describe_table(...)` | ✅ 返回字段列表 |
| 2. 执行查询 | `execute_query("local-test-mysql", "testdb", "SELECT name, department, salary FROM employees ORDER BY salary DESC LIMIT 3")` | ✅ 3 行数据 |

### instance-overview 工具链

| 步骤 | 工具调用 | 结果 |
|------|---------|------|
| 1. 列出实例 | `list_instances()` | ✅ 获取实例 id 映射 |
| 2. 查看账号 | `list_instance_accounts(30)` | ✅ 返回账号列表（含权限详情） |
| 3. 查看库 | `list_instance_databases(30)` | ✅ 返回 2 个库（archery, testdb） |

### Skills 清单

| # | Skill | 目录 | 触发方式 | 状态 |
|---|-------|------|---------|------|
| 1 | db-explore | `.claude/skills/db-explore/` | 自动 | ✅ |
| 2 | sql-query | `.claude/skills/sql-query/` | 自动 | ✅ |
| 3 | schema-doc | `.claude/skills/schema-doc/` | `/schema-doc` | ✅ |
| 4 | workflow-submit | `.claude/skills/workflow-submit/` | 自动 | ✅ |
| 5 | workflow-manage | `.claude/skills/workflow-manage/` | 自动 | ✅ |
| 6 | instance-overview | `.claude/skills/instance-overview/` | `/instance-overview` | ✅ |

## 六、已修复问题

| 问题 | 根因 | 修复方案 |
|------|------|---------|
| MCP 工具调用返回 "Error executing tool" | Docker 20.10.5 默认 seccomp profile 限制 `clone` 系统调用，容器内无法创建线程 | 容器启动加 `--security-opt seccomp=unconfined` |
| 同步代码在 MCP SDK 中触发 worker thread | `archery_client.py` 使用同步 httpx.Client，MCP SDK 用 `anyio.to_thread` 执行 | 将 client 和 server 全部改为 async（httpx.AsyncClient） |
