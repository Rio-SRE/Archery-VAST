# Archery 交接说明

日期：2026-10-08

## 1. 平台

- 产品：Archery v1.10.0（SQL 审核 / 查询 / 工单）
- 部署：阿里云 ECS `39.96.66.171`，K8s namespace `archery`
- 域名：archery.itripo3d.com（部分路径如 `/simsubmit/`、`/autoreview/` 可能被反代漏配，直连 `http://39.96.66.171:9123` 可用）

## 2. 账号

| 用途 | 用户 | 密码 / 密钥 |
|------|------|-------------|
| Archery Web / Admin | admin | Admin@2026! |
| Archery 元数据库 MySQL | root | Archery@2026! |
| Django SECRET_KEY | — | archery-cloudops-secret-key-2026 |
| 阿里云 AK | 见仓库外 `cloudops/aliyun.cfg`（不上 GitHub） |
| AWS AK | 见仓库外 `cloudops/aws.cfg`（不上 GitHub） |
| 百度云 | 见仓库外 `cloudops/baidu.cfg`（不上 GitHub） |

RDS 业务库账号分散在 `scripts/register_*.py`（如 `guozhenyu` / `Wuyu@2026!`、`tripo` / `Tripo3D!*`）。

## 3. 实例注册约定

- slave：标签 `支持查询` + 云厂商（阿里云=5 / aws=7），资源组 default(1)
- master：标签 `支持查询` + `支持上线` + 云厂商
- Django admin 多选字段 POST 名是英文：`resource_group`、`instance_tag`（不是中文 label）
- 查询页「查看表结构」依赖 `information_schema` 权限，连接用户必须能看到表（优先用 owner，如 `guozhenyu`）

## 4. 已知问题

- `tripo-studio`（pgm-2zeww8ry8w6a7093）：`tripo` / `Tripo3D!AiCoding` 认证失败，需补正确凭据
- AWS RDS 实例配额已从 45 提到 60（us-west-2）
- 新建 `tripo-prod-growth-open` / `-ro` 已注册：`aws-tripo-prod-growth-open` (id=109)、`aws-tripo-prod-growth-open-ro` (id=110)，主库密码 `Tripo3D!Growth2026`

## 5. 新 RDS（交接时在线）

主库：`tripo-prod-growth-open.c1eakwiuo7nt.us-west-2.rds.amazonaws.com:5432`  
从库：`tripo-prod-growth-open-ro.c1eakwiuo7nt.us-west-2.rds.amazonaws.com:5432`  
用户：`rdsroot` / `Tripo3D!Growth2026`  
安全组：`sg-06a186e757febdd84`（5432 对 0.0.0.0/0）
