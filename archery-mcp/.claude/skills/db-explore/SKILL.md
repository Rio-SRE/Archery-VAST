---
name: db-explore
description: 数据库探索。当用户想浏览数据库实例、查找表、查看字段结构时自动使用。触发词：找表、有哪些库、表结构、字段、列出数据库、schema。
---

# 数据库探索

通过 Archery MCP 快速浏览数据库元数据：实例、库、表、字段。

## 使用的 MCP 工具

- `list_instances` — 列出所有实例
- `list_databases(instance_name)` — 列出实例下的库
- `list_tables(instance_name, db_name, schema_name?)` — 列出表
- `describe_table(instance_name, db_name, tb_name, schema_name?)` — 查看字段

## 操作流程

1. 如果用户没有指定实例名，先调用 `list_instances` 列出所有可用实例，帮用户确认目标实例
2. 如果用户没有指定数据库，调用 `list_databases` 列出该实例下的库
3. 按需调用 `list_tables` 列出表，或 `describe_table` 查看字段

## 关键规则

- PostgreSQL 实例在调用 `list_tables` 和 `describe_table` 时必须传 `schema_name`，默认用 `"public"`
- 实例类型可从 `list_instances` 返回的 `db_type` 字段判断：`pgsql` 或 `mysql`
- 实例名区分大小写，务必使用 `list_instances` 返回的准确名称
- 输出时用表格格式展示结果，方便用户阅读
- 如果用户描述模糊（如"用户库"），先列出所有实例让用户选择，不要猜测

## 输出格式

- 实例列表：按类型分组（MySQL / PostgreSQL），显示名称、类型、读写模式
- 表列表：直接列出表名，数量多时分列显示
- 字段详情：用 Markdown 表格展示字段名列表
