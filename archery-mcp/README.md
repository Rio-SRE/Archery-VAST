# Archery MCP Server/Skill 使用手册

## 一、简介

Archery MCP Server 将 Archery SQL 审核平台的能力通过 MCP（Model Context Protocol）协议暴露给 AI 助手。研发同事在 Claude Code / Cursor 等工具中，可以直接用自然语言查询数据库、提交变更工单、审核工单，无需打开 Archery Web 页面。

## 二、服务信息

| 项目 | 值 |
|------|-----|
| MCP Server 地址 | http://39.96.66.171:8080/mcp |
| Archery Web UI | http://39.96.66.171:9123 |
| 协议 | MCP Streamable HTTP |
| 支持数据库 | MySQL 8.x、PostgreSQL 15/16/18 |
| 已接入实例数 | 34（阿里云 19 + 测试 1 + 其他） |
| 部署位置 | 阿里云 ECS cn-beijing（39.96.66.171） |

## 三、接入方式

### 3.1 Claude Code（推荐）

打开或创建项目目录下的 `.claude/settings.json`，添加：

```json
{
  "mcpServers": {
    "archery": {
      "type": "url",
      "url": "http://39.96.66.171:8080/mcp"
    }
  }
}
```

重启 Claude Code，打开终端输入：

```
有哪些数据库实例？
```

如果回复正常返回实例列表，说明接入成功。

### 3.2 Cursor

在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "archery": {
      "url": "http://39.96.66.171:8080/mcp"
    }
  }
}
```

重启 Cursor 后生效。

### 3.3 其他 MCP 客户端

任何支持 MCP Streamable HTTP transport 的客户端都可以接入，只需配置 URL：

```
http://39.96.66.171:8080/mcp
```

## 四、Tools 详细说明

### 4.1 实例管理

#### list_instances — 列出所有数据库实例

**输入**：无参数

**示例对话**：

```
用户：有哪些数据库实例？
```

**输出**（节选）：

```json
[
  {"id": 34, "name": "user-lifecycle-pg", "type": "pgsql", "host": "10.128.2.219", "port": 5432, "mode": "master"},
  {"id": 1, "name": "test-mysql", "type": "mysql", "host": "archery-mysql", "port": 3306, "mode": "master"},
  {"id": 2, "name": "bj-pg-algo-data", "type": "pgsql", "host": "10.124.1.126", "port": 5432, "mode": "master"},
  {"id": 3, "name": "bj-pg-tripo-data", "type": "pgsql", "host": "10.104.18.88", "port": 5432, "mode": "master"},
  ...
]
```

**说明**：返回所有在 Archery 中注册的实例，包含实例 ID、名称、类型（mysql/pgsql）、地址、端口、读写模式。

#### list_databases — 列出实例下的数据库

**输入**：`instance_name`（实例名称）

**示例对话**：

```
用户：帮我看看 local-test-mysql 有哪些数据库
```

**输出**：

```json
["archery", "testdb"]
```

**说明**：列出该实例上所有可用的数据库名。

#### list_tables — 列出数据库下的表

**输入**：`instance_name`（实例名）、`db_name`（数据库名）、`schema_name`（可选，PG 需传 "public"）

**示例对话**：

```
用户：testdb 里有哪些表
```

**输出**：

```json
["employees"]
```

**说明**：返回该数据库下所有表名。

#### describe_table — 查看表结构

**输入**：`instance_name`、`db_name`、`tb_name`、`schema_name`（可选）

**示例对话**：

```
用户：看看 testdb 的 employees 表有哪些字段
```

**输出**：

```json
["id", "name", "email", "department", "salary", "created_at"]
```

**说明**：返回该表所有列名，方便 AI 构造正确的 SQL。

### 4.2 SQL 查询

#### execute_query — 执行只读 SQL 查询

**输入**：`instance_name`、`db_name`、`sql`、`schema_name`（可选）、`limit`（可选，默认 100）

**示例对话**：

```
用户：帮我查一下 testdb 的 employees 表里工资最高的前 3 个人
```

**输出**：

```json
{
  "columns": ["id", "name", "email", "department", "salary", "created_at"],
  "rows": [
    [3, "Wang Wu", "wangwu@test.com", "Engineering", "18000.00", "2026-08-21 03:36:18"],
    [1, "Zhang San", "zhangsan@test.com", "Engineering", "15000.00", "2026-08-21 03:36:18"],
    [2, "Li Si", "lisi@test.com", "Product", "12000.00", "2026-08-21 03:36:18"]
  ],
  "row_count": 3
}
```

**说明**：执行 SELECT/SHOW 等只读查询。DML/DDL 语句（INSERT/UPDATE/DELETE/ALTER）会被拦截，提示走工单流程。

**错误示例**：

```
用户：删除 employees 表
```

**输出**：

```
Query error: 不支持的查询语法类型!
```

### 4.3 SQL 工单（变更管理）

#### submit_workflow — 提交 SQL 变更工单

**输入**：`workflow_name`、`instance_name`、`db_name`、`sql_content`、`group_id`（可选）

**示例对话**：

```
用户：提交一个工单，给 testdb 的 employees 表加一个 phone 字段
```

**输出**：

```json
{"status": "submitted", "workflow_id": 5}
```

**说明**：提交后进入审核队列，等待 DBA/管理员审批后执行。

#### list_workflows — 列出工单

**输入**：`limit`（可选，默认 20）

**示例对话**：

```
用户：看看有哪些待审核的工单
```

**输出**：

```json
[
  {"id": 5, "name": "add-phone-column", "status": "workflow_manreviewing"},
  {"id": 4, "name": "update-salary", "status": "workflow_finish"},
  {"id": 3, "name": "insert-test-data", "status": "workflow_finish"}
]
```

#### get_workflow — 获取工单详情

**输入**：`workflow_id`（工单 ID）

**示例对话**：

```
用户：工单 5 的详情是什么
```

**输出**：

```json
{"id": 5, "workflow_name": "add-phone-column", "status": "workflow_manreviewing"}
```

#### review_workflow — 审核工单

**输入**：`workflow_id`、`action`（"pass" 或 "reject"）、`remark`（备注）

**示例对话**：

```
用户：审核通过工单 5，备注：字段合理
```

**输出**：

```
ok
```

#### execute_workflow — 执行已审核的工单

**输入**：`workflow_id`

**示例对话**：

```
用户：执行工单 5
```

**输出**：

```
ok
```

**说明**：工单必须已通过审核（status=workflow_review_pass）才能执行。执行后可以在 Archery Web UI 中查看执行结果。

### 4.4 实例详情

#### list_instance_accounts — 查看实例数据库账号

**输入**：`instance_id`（数字 ID）

**示例对话**：

```
用户：看看实例 1 上有哪些数据库账号
```

**输出**：

```json
[
  {"user": "root", "host": "%"},
  {"user": "guozhenyu", "host": "%"},
  {"user": "testuser", "host": "%"}
]
```

#### list_instance_databases — 查看实例管理的数据库

**输入**：`instance_id`

**示例对话**：

```
用户：实例 34 管理哪些数据库
```

**输出**：

```json
["wuyu_db", "postgres", "template0", "template1"]
```

## 五、常见问题

**Q: 查询返回"实例不存在"？**
A: 检查实例名称是否与 Archery 中的一致（区分大小写）。先用 `list_instances` 查看可用实例列表。

**Q: PostgreSQL 查询报 schema 错误？**
A: PG 需要传 `schema_name` 参数，通常为 `"public"`。

**Q: 工单提交后没有执行？**
A: 工单需要审核。先 `review_workflow` 通过，再 `execute_workflow` 执行。

**Q: 查询被拦截报"不支持的查询语法类型"？**
A: 只允许 SELECT/SHOW 等只读操作。INSERT/UPDATE/DELETE/ALTER 需要提交工单。

**Q: 如何确认连接正常？**
A: 在 Claude Code 中输入"有哪些数据库实例？"，如果能返回实例列表说明连接正常。

## 六、权限说明

| 角色 | 能力 |
|------|------|
| dev_lead（默认） | 查询所有实例、提交工单、审核工单、执行工单 |
| 普通用户 | 只能查询已授权的库表 |

**注意**：所有操作都在 Archery 平台留痕（审计日志），可随时追溯。

## 七、运维管理

### 查看服务日志

```bash
ssh -i ~/.ssh/cloudpods_key root@39.96.66.171 'docker logs archery-mcp --tail 50'
```

### 重启服务

```bash
ssh -i ~/.ssh/cloudpods_key root@39.96.66.171 'docker restart archery-mcp'
```

### 更新部署

```bash
# 打包并上传
cd archery-mcp && tar czf /tmp/archery-mcp.tar.gz Dockerfile server.py archery_client.py
scp -i ~/.ssh/cloudpods_key /tmp/archery-mcp.tar.gz root@39.96.66.171:/opt/archery-mcp/

# 重建并重启（--security-opt seccomp=unconfined 是必需的，否则容器内无法创建线程）
ssh -i ~/.ssh/cloudpods_key root@39.96.66.171 'cd /opt/archery-mcp && tar xzf archery-mcp.tar.gz && docker build -t archery-mcp:latest . && docker rm -f archery-mcp && docker run -d --name archery-mcp --network host --security-opt seccomp=unconfined -e ARCHERY_URL=http://localhost:9123 -e ARCHERY_USERNAME=dev_lead -e ARCHERY_PASSWORD=LeadDev#2026!Secure archery-mcp:latest'
```

## 八、Skills（技能）

项目提供了 6 个 Claude Code Skills，帮助你更高效地通过自然语言操作数据库。

Skills 源文件位于本仓库的 `skills/` 目录下，需要安装到你自己项目中才能使用。

### 安装 Skills

将 `skills/` 目录复制到你项目的 `.claude/skills/` 下即可：

```bash
# 方式一：直接从仓库复制（如果你能访问 cloudops 仓库）
cp -r /path/to/cloudops/archery-mcp/skills/* 你的项目/.claude/skills/

# 方式二：手动创建目录结构
mkdir -p .claude/skills
cp -r archery-mcp/skills/* .claude/skills/
```

安装后的目录结构：

```
你的项目/
  .claude/
    skills/
      db-explore/SKILL.md
      sql-query/SKILL.md
      schema-doc/SKILL.md
      workflow-submit/SKILL.md
      workflow-manage/SKILL.md
      instance-overview/SKILL.md
    settings.json              ← 需要配置 MCP Server（见第三节）
```

> **前提**：你的项目需要先配置好 Archery MCP Server（见第三节 接入方式），Skills 才能正常工作。

### 使用方式

- **自动触发**：直接用自然语言描述需求，Claude 会自动匹配合适的 Skill
- **手动触发**：输入 `/skill名称`，如 `/schema-doc`、`/instance-overview`

### Skills 总览

| Skill | 触发方式 | 用途 |
|-------|---------|------|
| db-explore | 自动 | 浏览实例、库、表、字段 |
| sql-query | 自动 | 自然语言转 SQL 查数据 |
| workflow-submit | 自动 | 提交 DDL/DML 变更工单 |
| workflow-manage | 自动 | 审核、执行、跟踪工单 |
| schema-doc | `/schema-doc` | 生成表结构文档、Schema 对比 |
| instance-overview | `/instance-overview` | 实例巡检、账号安全检查 |

---

### 8.1 db-explore — 数据库探索

**触发方式**：自动（提到"有哪些库"、"找表"、"表结构"、"字段"等自然触发）

**功能**：逐层浏览数据库元数据 — 实例 → 库 → 表 → 字段。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `list_instances` | 无 | 列出所有实例 |
| `list_databases` | `instance_name` | 列出实例下的库 |
| `list_tables` | `instance_name`, `db_name`, `schema_name?` | 列出表 |
| `describe_table` | `instance_name`, `db_name`, `tb_name`, `schema_name?` | 查看字段 |

**示例对话**：

```
用户：有哪些数据库实例？
AI：（调用 list_instances，按 MySQL/PostgreSQL 分组展示 34 个实例）

用户：local-test-mysql 有哪些库？
AI：（调用 list_databases）archery、testdb

用户：testdb 里有什么表？
AI：（调用 list_tables）employees

用户：看看 employees 表的字段
AI：（调用 describe_table）id, name, email, department, salary, created_at
```

**注意事项**：

- PostgreSQL 实例查表和字段时需要 `schema_name`，默认为 `"public"`
- 实例名区分大小写，用 `list_instances` 返回的名称为准
- 从 `list_instances` 返回的 `db_type` 字段判断引擎类型：`mysql` 或 `pgsql`

---

### 8.2 sql-query — SQL 查询助手

**触发方式**：自动（提到"查一下"、"帮我查"、"统计"、"多少条"等自然触发）

**功能**：将自然语言转为 SQL，执行只读查询并展示结果。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `describe_table` | `instance_name`, `db_name`, `tb_name`, `schema_name?` | 先查表结构，确保列名正确 |
| `execute_query` | `instance_name`, `db_name`, `sql`, `schema_name?`, `limit?` | 执行 SELECT/SHOW 查询 |

**示例对话**：

```
用户：查一下 testdb 的 employees 表里工资最高的前 3 个人
AI：（先 describe_table 获取字段，再构造 SQL）
    SELECT name, department, salary FROM employees ORDER BY salary DESC LIMIT 3
    ┌──────────┬─────────────┬──────────┐
    │ name     │ department  │ salary   │
    ├──────────┼─────────────┼──────────┤
    │ Wang Wu  │ Engineering │ 18000.00 │
    │ Zhang San│ Engineering │ 15000.00 │
    │ Li Si    │ Product     │ 12000.00 │
    └──────────┴─────────────┴──────────┘

用户：统计每个部门有多少人
AI：SELECT department, COUNT(*) as cnt FROM employees GROUP BY department
    ...
```

**注意事项**：

- 只支持 SELECT / SHOW 等只读查询
- INSERT / UPDATE / DELETE / ALTER 会被 Archery 拦截，提示"不支持的查询语法类型"
- 如果需要修改数据，请使用 `workflow-submit`（提交工单）
- PostgreSQL 查询需要传 `schema_name="public"`
- 默认 `limit=100`，可在请求中指定更大值

---

### 8.3 workflow-submit — SQL 变更工单提交

**触发方式**：自动（提到"加字段"、"建表"、"改表"、"插入"、"删除"、ALTER/CREATE/DROP 等自然触发）

**功能**：将数据变更需求转为 SQL，通过 Archery 工单流程提交审核。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `describe_table` | `instance_name`, `db_name`, `tb_name`, `schema_name?` | 查看当前表结构 |
| `submit_workflow` | `workflow_name`, `instance_name`, `db_name`, `sql_content`, `group_id?` | 提交工单 |

**示例对话**：

```
用户：给 testdb 的 employees 表加一个 phone 字段
AI：当前 employees 表有 6 个字段：id, name, email, department, salary, created_at
    建议 SQL：
    ALTER TABLE employees ADD COLUMN phone VARCHAR(20) DEFAULT '' NOT NULL
    工单名称：add-phone-column
    确认提交吗？

用户：确认
AI：（调用 submit_workflow）工单已提交，ID: 6
    下一步：使用"审核通过工单 6"进行审核，审核通过后执行。
```

**注意事项**：

- AI 会先展示 SQL 让你确认，不会自动提交
- 工单名称为英文 kebab-case（如 `add-phone-column`）
- `group_id` 默认为 1，除非指定其他资源组
- 工单提交后需要审核通过 → 执行，完整流程见 `workflow-manage`

---

### 8.4 workflow-manage — 工单审核与执行管理

**触发方式**：自动（提到"工单"、"审核"、"审批"、"执行工单"、"通过"、"驳回"等自然触发）

**功能**：管理 SQL 变更工单的全生命周期 — 查看、审核、执行。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `list_workflows` | `limit?` | 列出最近工单 |
| `get_workflow` | `workflow_id` | 查看工单详情 |
| `review_workflow` | `workflow_id`, `action`, `remark?` | 审核：`action="pass"` 通过 / `"reject"` 驳回 |
| `execute_workflow` | `workflow_id` | 执行已审核工单 |

**工单状态流转**：

```
提交 → workflow_manreviewing（待审核）
     → workflow_review_pass（审核通过）→ workflow_finish（已执行）
     → workflow_abort（已驳回/终止）
```

**示例对话**：

```
用户：看看有哪些工单
AI：（调用 list_workflows）
    | ID | 名称              | 状态           |
    |----|-------------------|----------------|
    | 6  | add-phone-column  | 待审核         |
    | 5  | insert-test-data  | 已执行完成     |

用户：审核通过工单 6，备注：字段合理
AI：确认审核通过工单 6 吗？
用户：确认
AI：（调用 review_workflow(6, "pass", "字段合理")）审核通过。

用户：执行工单 6
AI：工单 6（add-phone-column）已审核通过，执行后不可撤回，确认执行？
用户：确认
AI：（调用 execute_workflow(6)）执行成功。
```

**注意事项**：

- 审核和执行操作前 AI 会要求你确认
- 驳回工单时必须填写原因
- 只有 `workflow_manreviewing` 状态可以审核
- 只有 `workflow_review_pass` 状态可以执行

---

### 8.5 schema-doc — 表结构文档生成

**触发方式**：手动，输入 `/schema-doc` 后描述需求

**功能**：批量获取表结构，生成 Markdown 文档；或对比两个库的 Schema 差异。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `list_tables` | `instance_name`, `db_name`, `schema_name?` | 列出表 |
| `describe_table` | `instance_name`, `db_name`, `tb_name`, `schema_name?` | 获取字段 |

**示例对话**：

```
用户：/schema-doc
      帮我生成 local-test-mysql testdb 的表结构文档

AI：## testdb 数据库文档
    实例：local-test-mysql | 表数量：1

    ### employees
    | 字段 | 类型 |
    |------|------|
    | id   | int  |
    | name | varchar(100) |
    | ...  | ...  |
```

```
用户：/schema-doc
      对比 bj-pg-vast-tripo-2 的 wuyu_db 和 bj-pg-vast-tripo-8 的 wuyu_db

AI：（分别获取两边的表和字段，输出差异报告）
    仅在 A 中存在的表：...
    仅在 B 中存在的表：...
    同名表字段差异：...
```

**注意事项**：

- PostgreSQL 需要 `schema_name="public"`
- 表数量超过 30 时，AI 会先列出表清单让你选择
- 默认在回复中输出文档，如需写入文件请明确说明

---

### 8.6 instance-overview — 实例总览与账号检查

**触发方式**：手动，输入 `/instance-overview` 后描述需求

**功能**：汇总实例信息、检查数据库账号配置，用于日常巡检和安全审计。

**调用的 MCP 工具**：

| 工具 | 参数 | 说明 |
|------|------|------|
| `list_instances` | 无 | 列出所有实例（含 id） |
| `list_instance_accounts` | `instance_id`（数字 ID） | 查看账号列表 |
| `list_instance_databases` | `instance_id`（数字 ID） | 查看管理的库 |

**示例对话**：

```
用户：/instance-overview
      看看所有实例的概况

AI：## 实例总览
    总计 34 个实例 | MySQL: 8 | PostgreSQL: 26 | Master: 32 | Slave: 2
    （按类型分组展示实例表格）
```

```
用户：/instance-overview
      做一次账号安全检查，看看有没有高风险账号

AI：（遍历各实例调用 list_instance_accounts）
    ⚠️ 高风险项：
    - local-test-mysql: root@% — 允许任意来源连接
    - ...
    ✅ 正常项：
    - bj-mysql-api-1: guozhenyu@10.% — 限制内网访问
    - ...
```

**注意事项**：

- `list_instance_accounts` 和 `list_instance_databases` 需要数字 `instance_id`，不是实例名
- AI 会先调用 `list_instances` 获取 id 与 name 的映射
- 全量巡检涉及 34 个实例，耗时较长，AI 会分批展示结果
- 安全检查会标记：host 为 `%` 的账号、root/admin 开放远程访问等风险项
