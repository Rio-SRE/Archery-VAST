---
name: schema-doc
description: 表结构文档生成。当用户要求生成数据库文档、导出表结构、对比 schema 时使用。手动触发。
disable-model-invocation: true
---

# 表结构文档生成

批量获取表结构信息，生成 Markdown 格式的数据库文档。

## 使用的 MCP 工具

- `list_databases(instance_name)` — 列出库
- `list_tables(instance_name, db_name, schema_name?)` — 列出表
- `describe_table(instance_name, db_name, tb_name, schema_name?)` — 获取字段

## 操作流程

### 单库文档生成

1. 用户指定实例和数据库
2. 调用 `list_tables` 获取所有表
3. 对每张表调用 `describe_table` 获取字段
4. 输出结构化 Markdown 文档，包含：
   - 数据库概览（实例名、库名、表数量）
   - 每张表的字段列表

### 跨库 Schema 对比

1. 用户指定两个目标（可以是不同实例的不同库）
2. 分别获取两边的表和字段信息
3. 对比输出：
   - 仅在 A 中存在的表
   - 仅在 B 中存在的表
   - 同名表的字段差异

## 关键规则

- PostgreSQL 实例需要传 `schema_name="public"`
- 表数量较多时（>30），先列出表清单让用户选择要生成文档的表
- 直接在回复中输出文档内容，不要创建文件，除非用户明确要求写入文件
- 对比时注意不同数据库类型的字段命名差异（如 MySQL 的 INT vs PostgreSQL 的 integer）
