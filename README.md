# Archery-VAST

VAST / Tripo 内部 Archery SQL 审核平台交接仓库：部署清单、自定义补丁、MCP、运维脚本、实例录入表和账号密钥。

> 本仓库含生产凭据，仅限内部交接使用。不要公开。

## 在线地址

| 服务 | 地址 |
|------|------|
| Archery Web | http://archery.itripo3d.com 或 http://39.96.66.171:9123 |
| MCP Server | http://39.96.66.171:8080/mcp |
| 管理后台 | http://archery.itripo3d.com/admin/ |

## 目录

```
.
├── k8s/                 # K8s 部署（Deployment / Secret / 监控补丁）
├── archery-custom/      # Archery 源码补丁（views / urls / instance 监控）
├── archery-mcp/         # MCP Server + Skills
├── scripts/             # 实例注册、连通性验证、RBAC
├── docs/                # 使用手册、用户清单、RDS 录入表
├── credentials/         # 云账号 AK/SK、Archery 登录密码
└── docker-compose.yml   # 本地/单机 Docker 部署
```

## 登录

- 用户名：`admin`
- 密码：`Admin@2026!`

其他账号见 [docs/archery_user_list.csv](docs/archery_user_list.csv)。默认密码同样为 `Admin@2026!`（以实际为准）。

## 部署（K8s）

```bash
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/mysql.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/archery.yaml
bash k8s/deploy-monitor.sh
```

镜像：`hhyo/archery:v1.10.0`。MySQL root 密码和 Django `SECRET_KEY` 在 `k8s/secrets.yaml`。

## MCP

见 [archery-mcp/README.md](archery-mcp/README.md)。环境变量模板：`archery-mcp/.env.example`，生产密码见 `credentials/`。

## 交接要点

详见 [docs/HANDOVER.md](docs/HANDOVER.md)。
