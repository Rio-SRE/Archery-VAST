---
name: workflow-submit
description: SQL 变更工单提交。当用户要修改表结构、插入/更新/删除数据时自动使用。触发词：加字段、建表、改表、插入、更新、删除、ALTER、CREATE、DROP。
---

# SQL 变更工单提交

将用户的数据变更需求转为 SQL，通过 Archery 工单流程提交审核。

## 使用的 MCP 工具

- `describe_table(instance_name, db_name, tb_name, schema_name?)` — 查看当前表结构
- `execute_query(instance_name, db_name, sql, schema_name?)` — 查验当前数据
- `submit_workflow(workflow_name, instance_name, db_name, sql_content, group_id?)` — 提交工单

## 操作流程

1. 确认目标实例和数据库
2. 调用 `describe_table` 查看当前表结构，确认变更合理
3. 根据需求生成 DDL/DML 语句
4. 将 SQL 展示给用户确认，说明变更内容和影响范围
5. 用户确认后，生成工单名称（kebab-case，简明描述变更内容）
6. 调用 `submit_workflow` 提交
7. 返回工单 ID，提示用户后续审核和执行流程

## 关键规则

- 提交前必须将完整 SQL 展示给用户确认，不要自动提交
- 工单名称用英文 kebab-case（如 `add-phone-column`、`update-salary-range`）
- DDL 变更（ALTER / CREATE / DROP）影响大，提交前说明风险
- 批量 DML（UPDATE / DELETE 无 WHERE 或影响范围大）要特别警告
- `group_id` 默认为 1，除非用户指定其他资源组
- 提交成功后提醒：工单需要审核通过后才能执行，可以用 `/workflow-manage` 跟踪

## SQL 编写规范

- DDL 语句末尾不加分号（Archery 规范）
- 每条语句单独一行
- ALTER TABLE 建议每次只做一个变更，避免回滚困难
- 加字段时指定合理的默认值和 NOT NULL 约束
