---
name: sql-query
description: SQL 查询助手。当用户需要查数据、写 SQL、分析表数据时自动使用。触发词：查一下、帮我查、SELECT、多少条、统计、数据。
---

# SQL 查询助手

将用户的自然语言需求转为 SQL，通过 Archery MCP 执行只读查询并展示结果。

## 使用的 MCP 工具

- `describe_table(instance_name, db_name, tb_name, schema_name?)` — 查看表结构
- `execute_query(instance_name, db_name, sql, schema_name?, limit?)` — 执行查询
- `list_instances` / `list_databases` / `list_tables` — 按需定位目标

## 操作流程

1. 确认目标实例和数据库。如果用户未指定，用 `list_instances` 帮助定位
2. 调用 `describe_table` 获取目标表的字段信息，确保 SQL 中使用正确的列名
3. 根据用户需求编写 SELECT 语句
4. 调用 `execute_query` 执行，默认 limit=100
5. 将结果格式化为 Markdown 表格展示给用户
6. 如果用户需要进一步分析，在本地对返回数据做汇总计算

## 关键规则

- 只能执行 SELECT / SHOW 等只读查询。INSERT / UPDATE / DELETE / ALTER 会被 Archery 拦截
- 如果用户要修改数据，引导使用 `/workflow-submit` 提交工单
- PostgreSQL 查询必须传 `schema_name`（通常为 `"public"`）
- 先查表结构再写 SQL，避免列名错误
- 大表查询务必加 WHERE 条件或 LIMIT，避免返回过多数据
- SQL 中避免使用 `SELECT *`，明确列出需要的字段
- 返回结果超过 20 行时，先展示前 10 行，提示用户是否查看完整结果

## 错误处理

- "实例不存在" → 用 `list_instances` 确认名称后重试
- "不支持的查询语法类型" → 告诉用户该操作需要走工单流程
- 查询超时或报错 → 检查 SQL 语法，简化查询后重试
