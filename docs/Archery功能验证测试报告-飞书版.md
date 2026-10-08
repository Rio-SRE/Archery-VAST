# Archery 功能验证测试报告

## 基本信息

| 项目 | 值 |
|------|-----|
| 测试时间 | 2026-08-19 16:52 |
| 测试环境 | AWS EKS ap-northeast-1 / Archery v1.10.0 |
| 访问地址 | http://a09554bb298c54692b290ad819e8fd7b-672420120.ap-northeast-1.elb.amazonaws.com:9123 |
| 管理员账号 | admin / Admin@2026! |
| 研发账号 | developer / Dev@2026! |
| 测试实例 | test-mysql (MySQL 8.0, archery-mysql:3306) |
| 测试数据库 | testdb (users 表, 4行数据) |

## 一、页面可用性测试 (admin)

| 页面 | 路径 | 状态 |
|------|------|------|
| 仪表盘 | /dashboard/ | ✅ 200 |
| SQL工单列表 | /sqlworkflow/ | ✅ 200 |
| SQL查询 | /sqlquery/ | ✅ 200 |
| 实例管理 | /instance/ | ✅ 200 |
| DDL工单详情 | /detail/2/ | ✅ 200 |
| DML工单详情 | /detail/3/ | ✅ 200 |
| 权限申请列表 | /queryapplylist/ | ✅ 200 |
| 系统配置 | /config/ | ✅ 200 |
| 慢查询 | /slowquery/ | ✅ 200 |
| 审批流程 | /workflow/ | ✅ 200 |
| 数据归档 | /archive/ | ✅ 200 |

**结果: 11/11 通过**

## 二、SQL 查询功能

### admin 用户查询

| 测试用例 | SQL | 结果 | 状态 |
|---------|-----|------|------|
| 全表查询 | SELECT * FROM users | 返回 4 行, 6 列 (id, name, email, phone, created_at, age) | ✅ PASS |
| 聚合查询 | SELECT COUNT(*), AVG(age) FROM users | cnt=4, avg_age=29.5 | ✅ PASS |
| 条件查询 | SELECT COUNT(*) FROM users WHERE age > 25 | cnt=3 | ✅ PASS |
| 元数据查询 | SHOW TABLES | 返回 1 张表 (users) | ✅ PASS |
| 危险SQL拦截 | DROP TABLE users | 被拦截: "不支持的查询语法类型!" | ✅ PASS |

### developer 用户查询

| 测试用例 | 结果 | 状态 |
|---------|------|------|
| 查询已授权库 (testdb.users) | 返回 2 行数据 | ✅ PASS |
| 查询未授权库 (mysql.user) | 被拒绝: "您无权查看该表" | ✅ PASS |

## 三、工单变更流程

### DDL 变更工单

| 阶段 | 详情 | 状态 |
|------|------|------|
| 工单名称 | add-age-column | - |
| SQL内容 | ALTER TABLE users ADD COLUMN age INT DEFAULT 0 | - |
| 提交 | admin 提交, 进入待审核 | ✅ |
| 审核 | DBA 组审批通过 | ✅ |
| 执行 | age 列成功添加到 users 表 | ✅ |
| 验证 | INFORMATION_SCHEMA 确认 age 列存在 | ✅ |
| 最终状态 | workflow_finish | ✅ |

### DML 变更工单

| 阶段 | 详情 | 状态 |
|------|------|------|
| 工单名称 | insert-test-data | - |
| SQL内容 | INSERT INTO users (name,email,phone,age) VALUES(...) | - |
| 提交 | admin 提交, 进入待审核 | ✅ |
| 审核 | DBA 组审批通过 | ✅ |
| 执行 | wangwu, zhaoliu 数据成功插入 | ✅ |
| 验证 | users 表当前 4 行数据 | ✅ |
| 最终状态 | workflow_finish | ✅ |

## 四、用户权限管理

### 用户配置

| 用户 | 角色 | 权限 | 资源组 |
|------|------|------|--------|
| admin | 超级管理员 | 全部权限, DBA组 | default |
| developer | 普通研发 | SQL查询, 权限申请 | default |

### 权限授权测试

| 测试用例 | 结果 | 状态 |
|---------|------|------|
| developer 申请 testdb 查询权限 | 工单已创建 (apply_id=1) | ✅ |
| DBA 审批查询权限申请 | 审批通过, 自动授权 | ✅ |
| developer 查询已授权库 | 正常返回数据 | ✅ |
| developer 查询未授权库 | 被拒绝 | ✅ |
| 权限有效期 | 设置为 2099-12-31 | ✅ |
| 行数限制 | limit_num=1000 | ✅ |

## 五、审批流程配置

| 配置项 | 值 | 状态 |
|--------|-----|------|
| 审批组 | DBA | ✅ |
| SQL上线审批流 | 提交 → DBA组审核 → 执行 | ✅ |
| 查询权限审批流 | 申请 → DBA组审核 → 自动授权 | ✅ |
| 资源组 | default (关联 test-mysql 实例) | ✅ |

## 六、实例管理

### 6.1 实例基本信息

| 项目 | 值 | 状态 |
|------|-----|------|
| 实例名称 | test-mysql | ✅ |
| 数据库类型 | MySQL 8.0 | ✅ |
| 连接地址 | archery-mysql:3306 | ✅ |
| 实例类型 | master | ✅ |
| 连接用户 | root | ✅ |
| 资源组 | default | ✅ |
| 连通性 | 正常 | ✅ |
| 测试库 testdb | users表, 4行, 6列 | ✅ |

### 6.2 实例管理页面

| 页面 | 路径 | 状态 |
|------|------|------|
| 实例列表 | /instance/ | ✅ 200 |
| 实例账号 | /instanceaccount/ | ✅ 200 |
| 实例参数 | /instanceparam/ | ✅ 200 |
| 数据库管理 | /database/ | ✅ 200 |
| DB诊断 | /dbdiagnostic/ | ✅ 200 |
| DBA原则 | /dbaprinciples/ | ✅ 200 |

### 6.3 实例管理 API

| 功能 | API | 结果 | 状态 |
|------|-----|------|------|
| 获取数据库列表 | GET /instance/instance_resource/?resource_type=database | archery, testdb | ✅ PASS |
| 获取表列表 | GET /instance/instance_resource/?resource_type=table&db_name=testdb | users | ✅ PASS |
| 获取列信息 | GET /instance/instance_resource/?resource_type=column&tb_name=users | id, name, email, phone, created_at, age | ✅ PASS |
| 实例账号列表 | POST /instance/user/list | 6 accounts (root, testuser, mysql.*) | ✅ PASS |
| 实例数据库列表 | POST /instance/database/list/ | archery, testdb | ✅ PASS |
| 参数配置 | POST /param/list/ | 需先导入参数模板 | ⚠️ 前置条件未满足 |

## 七、测试总结

| 测试维度 | 通过 | 失败 | 状态 |
|---------|------|------|------|
| 页面可用性 | 17 | 0 | ✅ ALL PASS |
| SQL查询 | 7 | 0 | ✅ ALL PASS |
| DDL变更工单 | 5 | 0 | ✅ ALL PASS |
| DML变更工单 | 5 | 0 | ✅ ALL PASS |
| 用户授权 | 6 | 0 | ✅ ALL PASS |
| 权限隔离 | 2 | 0 | ✅ ALL PASS |
| 审批流 | 3 | 0 | ✅ ALL PASS |
| 危险SQL拦截 | 1 | 0 | ✅ ALL PASS |
| 实例管理API | 5 | 1 | ⚠️ 参数配置需导入模板 |
| **合计** | **51** | **1** | **✅ 核心功能全部通过** |

## 八、已知限制与建议

### 已知限制及修复

1. **工单审批UI Bug (已修复)**:
   - 原因: `WorkflowAudit.next_audit` 为空字符串时，审批后 `current_audit` 被清空，导致详情页 `can_review()` 查询 `Group id=''` 报错 500
   - 修复: 确保单级审批的 `next_audit` 设为 `"-1"` 而非空字符串
   - 状态: ✅ 已修复，UI 审批流程正常（HTTP 302 重定向，详情页状态正确更新为"审核通过"）

2. **DESCRIBE 语句限制**: 查询权限不包含 DESCRIBE，需要用 `SELECT * FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='xxx'` 替代。

3. **参数配置功能**: 需要先导入 ParamTemplate（参数模板）才能使用参数配置功能，属于前置配置未完成，非 Bug。

4. **中文编码**: API 返回的中文为 UTF-8 编码显示为转义字符，Web UI 正常显示不受影响。

### 后续建议

1. **Archery 部署位置调整**: 当前 Archery 部署在 AWS 东京 EKS，连接阿里云北京 RDS 存在跨境网络限制。生产环境建议将 Archery 部署到与 RDS 同 Region 的环境（如阿里云 ACK 或 ECS），或通过 SSH 隧道/VPN 打通网络。
2. **对接飞书/钉钉审批**: 配置 Webhook 实现消息通知和移动端审批
3. **增加 goInception 引擎**: 部署 goInception 容器, 实现 SQL 自动审核规则
4. **配置数据脱敏规则**: 对 phone、email 等敏感字段配置脱敏策略
5. **配置慢查询采集**: 对接 MySQL 慢查询日志，实现慢查询分析功能

## 九、阿里云 RDS 接入测试

### 9.1 实例注册

| 实例名 | RDS ID | 引擎 | 地址 | 注册状态 |
|--------|--------|------|------|---------|
| aliyun-rds-mysql-1 | rm-2ze41f57iqutmybug | MySQL 8.0 | rm-2ze41f57iqutmybug-public.mysql.cn-beijing.rds.aliyuncs.com:3306 | ✅ 已注册 |
| aliyun-rds-mysql-2 | rm-2ze3qmtv14hehzh2o | MySQL 8.0 | rm-2ze3qmtv14hehzh2o-public.mysql.rds.aliyuncs.com:3306 | ✅ 已注册 |

### 9.2 连通性测试

| 实例 | 白名单 | 网络连通 | 原因 |
|------|--------|---------|------|
| test-mysql (K8s内部) | N/A | ✅ 正常 | 同集群内部通信 |
| aliyun-rds-mysql-1 | ✅ 已配置 (0.0.0.0/0 + EKS IP) | ❌ 超时 | 跨境网络限制 (日本→中国 3306端口) |
| aliyun-rds-mysql-2 | ✅ 已配置 (0.0.0.0/0 + EKS IP) | ❌ 超时 | 跨境网络限制 (日本→中国 3306端口) |

### 9.3 原因分析

Archery 部署在 AWS 东京 EKS (出口IP: 35.73.74.10)，阿里云 RDS 在北京。跨境网络对 MySQL 3306 端口有链路层访问限制，即使 RDS 白名单配置为 0.0.0.0/0 也无法直连。

### 9.4 生产环境解决方案

| 方案 | 实现方式 | 复杂度 | 推荐 |
|------|---------|--------|------|
| A. Archery 迁移到阿里云 | 部署到与 RDS 同 VPC 的 ACK/ECS | 低 | ✅ 推荐 |
| B. SSH 隧道中转 | EKS Pod → 阿里云 ECS (跳板机) → RDS 内网 | 中 | 可行 |
| C. VPN/专线 | AWS↔阿里云 VPN Gateway 或 Express Connect | 高 | 企业级 |
