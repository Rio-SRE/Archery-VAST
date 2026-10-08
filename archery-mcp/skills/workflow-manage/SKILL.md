---
name: workflow-manage
description: 工单审核与执行管理。当用户查看工单状态、审核工单、执行工单时自动使用。触发词：工单、审核、审批、执行工单、通过、驳回、工单状态。
---

# 工单审核与执行管理

管理 Archery SQL 变更工单的全生命周期：查看、审核、执行。

## 使用的 MCP 工具

- `list_workflows(limit?)` — 列出最近工单
- `get_workflow(workflow_id)` — 查看工单详情
- `review_workflow(workflow_id, action, remark?)` — 审核（通过/驳回）
- `execute_workflow(workflow_id)` — 执行已审核工单

## 工单状态说明

| 状态 | 含义 | 可执行操作 |
|------|------|-----------|
| `workflow_manreviewing` | 待审核 | review_workflow (pass/reject) |
| `workflow_review_pass` | 审核通过 | execute_workflow |
| `workflow_finish` | 已执行完成 | 无 |
| `workflow_abort` | 已终止/驳回 | 无 |

## 操作流程

### 查看工单

1. 调用 `list_workflows` 获取最近工单列表
2. 用表格展示工单 ID、名称、状态
3. 如需详情，调用 `get_workflow` 查看具体工单

### 审核工单

1. 调用 `get_workflow` 确认工单处于 `workflow_manreviewing` 状态
2. 展示工单内容给用户
3. 用户确认审核意见后，调用 `review_workflow`：
   - 通过：`action="pass"`
   - 驳回：`action="reject"`，附上 `remark` 说明原因

### 执行工单

1. 调用 `get_workflow` 确认工单处于 `workflow_review_pass` 状态
2. 提醒用户执行后不可撤回
3. 用户确认后调用 `execute_workflow`

## 关键规则

- 审核和执行操作前必须获得用户明确确认
- 驳回工单时必须填写 remark 说明原因
- 只有 `workflow_review_pass` 状态的工单才能执行
- 只有 `workflow_manreviewing` 状态的工单才能审核
- 状态不匹配时，向用户解释当前状态和可用操作
