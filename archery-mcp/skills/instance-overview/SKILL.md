---
name: instance-overview
description: 实例总览与账号检查。查看所有实例信息、数据库账号列表、实例下的库。用于日常巡检和安全审计。手动触发。
disable-model-invocation: true
---

# 实例总览与账号检查

汇总所有数据库实例信息，检查账号配置，用于日常巡检和安全审计。

## 使用的 MCP 工具

- `list_instances(scope)` — 列出实例。scope: manual / imported / all
- `list_instance_accounts(instance_id)` — 查看实例数据库账号
- `list_instance_databases(instance_id)` — 查看实例管理的库
- `get_instance_health(instance_id)` — 单实例健康巡检、延迟、连接水位、QPS 水位
- `analyze_instance_capacity(scope, warn_pct, crit_pct, limit)` — 批量分析水位，输出异常和热点实例

## 操作流程

### 实例总览

1. 调用 `list_instances` 获取全部实例
2. 按类型分组（MySQL / PostgreSQL）展示
3. 输出汇总统计：总实例数、各类型数量、master/slave 分布

### 单实例详情

1. 从 `list_instances` 获取目标实例的数字 `id`
2. 调用 `list_instance_accounts` 查看账号列表
3. 调用 `list_instance_databases` 查看管理的库
4. 汇总展示

### 账号安全检查

1. 遍历用户指定的实例（或全部实例）
2. 对每个实例调用 `list_instance_accounts`
3. 标记风险项：
   - host 为 `%` 的账号（允许任意来源连接）
   - 账号名为 `root` 或 `admin` 且 host 为 `%`
   - 同一账号出现在多个实例上

### 容量与健康分析

1. 调用 `analyze_instance_capacity`，默认 warn=60%、crit=80%
2. 关注 `down_or_error`（巡检失败）和 `warning_or_critical`（水位告警）
3. 单实例详情用 `get_instance_health`
4. 水位字段含义：`conn`/`qps` 为 `当前值 / 预估上限 (水位%)`

- `list_instance_accounts` 和 `list_instance_databases` 需要数字 `instance_id`，不是实例名
- 先调用 `list_instances` 获取 id 与 name 的映射关系
- 实例数量较多（34个），全量巡检时分批展示结果
- 安全检查结果按风险等级排序：高风险项排在前面
- 输出建议使用表格格式，便于对比和审阅
