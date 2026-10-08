# 阿里云 K8S Secret/ConfigMap 提取的 RDS 实例（Archery 录入格式）

扫描范围：12 个 ACK 集群（3 个可达，4 个 SSL 不通，5 个 RBAC 403）
可达集群：tripo_bj_test_service、tripo_bj_service、deliveryx-ack
共 11 条唯一实例（按 host+port 去重，过滤 Redis/MongoDB/monitor 账号）

| 实例名称 | 类型 | 引擎 | HOST | PORT | 用户名 | 密码 | 数据库 | 来源集群 | Secret | 备选账号 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ali-pgm-2zecx6rl341ps06d-tripo_commercial_app | master | pgsql | pgm-2zecx6rl341ps06d.pg.rds.aliyuncs.com | 5432 | tripo_commercial_app | tkJJ8PAJZySTmKtHbXDgUlaf8Yc7cj6LfqsAq_AM4C4 | ali_tripo_commercial | tripo_bj_test_service | commercial-postgres | tripo_studio/growth; vast_project_management_app/vast_project_management |
| ali-pgm-2ze8z17f8hp2t2be-tripo | master | pgsql | pgm-2ze8z17f8hp2t2be.pg.rds.aliyuncs.com | 5432 | tripo | Tripo3D!AiCoding | litellm | tripo_bj_service,tripo_bj_test_service | litellm-relay-env |  |
| ali-pgm-2ze65e3917t7412a-alipay_notify_gateway | master | pgsql | pgm-2ze65e3917t7412a.pg.rds.aliyuncs.com | 5432 | alipay_notify_gateway | 0f282775d374aced269e2d15a0aca8b4477ed973754f2404 | trade-alipay | tripo_bj_test_service | alipay-notify-gateway-secrets | tripo_commercial_app/commercial |
| ali-pgr-2ze9255ry42w60l6-commercial_readonly | slave | pgsql | pgr-2ze9255ry42w60l6.pg.rds.aliyuncs.com | 5432 | commercial_readonly | Ro!d5de5d1ce5e074426b4ca6abeb68 | commercial | tripo_bj_service | commercial-postgres-readonly |  |
| ali-pgm-2zeh3appfem428a3-tripo | master | pgsql | pgm-2zeh3appfem428a3.pg.rds.aliyuncs.com | 5432 | tripo | Tripo3D!Security | tripo_security_tns | tripo_bj_service | tns-server-env |  |
| ali-pgm-2ze3a5y6143le521-tripo | master | pgsql | pgm-2ze3a5y6143le521.pg.rds.aliyuncs.com | 5432 | tripo | Tripo3D!App | tripo_app | tripo_bj_service | tripo-app-service |  |
| ali-pgm-2zefzl63t3s1hx7w-tripo | master | pgsql | pgm-2zefzl63t3s1hx7w.pg.rds.aliyuncs.com | 5432 | tripo | Tripo3D!Growth | tripo_growth | tripo_bj_service | tripo-attribution-secrets |  |
| ali-pgm-2zev0241m73l2x3s-tripo | master | pgsql | pgm-2zev0241m73l2x3s.pg.rds.aliyuncs.com | 5432 | tripo | Tripo3D!Idp | tripo_base_idp | tripo_bj_service | tripo-idp-secret |  |
| ali-pgm-2zejr529xwzx20hz-tripo_arch | master | pgsql | pgm-2zejr529xwzx20hz.pg.rds.aliyuncs.com | 5432 | tripo_arch | 671d082e1e1c | tripo_base_svc_upload | tripo_bj_service | upload-postgres |  |
| ali-rm-2ze3qmtv14hehzh2o-public-guozhenyu | master | mysql | rm-2ze3qmtv14hehzh2o-public.mysql.rds.aliyuncs.com | 3306 | guozhenyu |  | ali_nacos | tripo_bj_test_service | cm:nacos-config |  |
| ali-rm-2ze41f57iqutmybug-tripo_arch | master | mysql | rm-2ze41f57iqutmybug.mysql.cn-beijing.rds.aliyuncs.com | 3306 | tripo_arch |  | nacos_cn | tripo_bj_service | cm:nacos-config |  |

## 不可达集群

| 集群 | 原因 | 建议 |
| --- | --- | --- |
| infra-k8s-test | SSL EOF（内网 API） | 从集群节点或跳板机扫描 |
| Data-cluster | SSL EOF（内网 API） | 从集群节点或跳板机扫描 |
| tripo | SSL EOF（内网 API） | 从集群节点或跳板机扫描 |
| holy-molly | SSL EOF（内网 API） | 从集群节点或跳板机扫描 |
| data-process-new | RBAC 403 | 需给 kubeconfig 用户授权 cluster-admin 或 secret 读权限 |
| data-process-old | RBAC 403 | 同上 |
| de-data-platform | RBAC 403 | 同上 |
| algo-inference-cluster | RBAC 403 | 同上 |
| algo-training-A100 | RBAC 403 | 同上 |
