# AWS EKS Secret/ConfigMap 提取的 RDS 实例（Archery 录入格式）

扫描范围：9 个 EKS 集群（7 个可达，2 个 401 未授权）
可达集群：Infra、Observability、Vast-Service、devops-cluster、tripo-dev-service、tripo-fe-cluster、cloudops-eks
不可达集群：bau-dev (401)、de-data-platform (401)

去掉已在 Archery 的 17 条，剩余 **13 条新实例**需录入：

| 实例名称 | 类型 | 引擎 | HOST | PORT | 用户名 | 密码 | 数据库 | 来源集群 | Secret | 备选账号 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| aws-identites-main-kratos-kratos | master | pgsql | identites-main-kratos.proxy-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | kratos | V0?8Ahju!J6.rvd0pmu:sVfLTubcnV# | kratos | Infra | tripo-idp-secret |  |
| aws-litellm-business-relay-litellm | master | pgsql | litellm-business-relay.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | litellm | H2a1*qLfB*0Q | litellm | Vast-Service | litellm-business-relay-env |  |
| aws-tripo-prod-commercial-tripo_commercial_app | master | pgsql | tripo-prod-commercial.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | tripo_commercial_app | 1df5704ac99531986ec4a66f90ca8a30f6b22240885edb1ecf59c63872970b50 | commercial | Vast-Service | commercial-postgres | coupon_user/sales_coupon; trade_promo_credit_rw/trade-promo-credit |
| aws-user=rdsroot password=jcmfApAk-tripo_growth | master | pgsql | user=rdsroot password=jcmfApAkHWXJYLVTdMPFMVJbCwbN7uAt host=production-tripo-read1.c1eakwiuo7nt.us-west-2.rds.amazonaws.com port=5432 dbname=tripo | 5432 | tripo_growth | 3TEE]YxomFM13=9 | tripo_growth | Vast-Service | referral-core-env |  |
| aws-tripo-prod-security-rdsroot | master | pgsql | tripo-prod-security.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | rdsroot | bXL98idKPwHrU7wz | tripo_prod_security | Vast-Service,tripo-dev-service | risk-bot-env,risk-env | tns_user/tns_svc |
| aws-tripo-prod-app-tripo | master | pgsql | tripo-prod-app.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | tripo | Tripo3D!App | tripo_app | Vast-Service | tripo-app-service |  |
| aws-database-community-rdsroot | master | pgsql | database-community.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | rdsroot | JZ~)rQ3YlXk2)v~[tyF_-rvhY7WU | tripo_community_exp_prod | Vast-Service | tripo-community-core-exp-sk,tripo-community-core-interaction | aigc_runtime/ |
| aws-community-task-rdsroot | master | pgsql | community-task.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | rdsroot | X2.Xd0.rfi#(_~##lvQa!Dn5[svg | tripo_community_task_prod | Vast-Service | tripo-community-svc-creator-growth-secret |  |
| aws-tripo-prod-base-user-tripo_base | master | pgsql | tripo-prod-base-user.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | tripo_base | &YeErjGXizMVd8h | tripo_base_user | Vast-Service | upload-postgres |  |
| aws-tripo-prod-base-user-tripo_base | master | pgsql | tripo-prod-base-user.cluster-ro-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | 5432 | tripo_base | &YeErjGXizMVd8h | tripo_base_user | Vast-Service,tripo-dev-service | hermes-agent-secret,risk-bot-env |  |
| aws-user=rdsroot password=K0URYt69-rdsroot | master | pgsql | user=rdsroot password=K0URYt69hEUbKSauiPt9 host=tripo-test.c1eakwiuo7nt.us-west-2.rds.amazonaws.com port=5432 dbname=tripo | 5432 | rdsroot | K0URYt69hEUbKSauiPt9 | growth | tripo-dev-service | referral-core-env |  |
| aws-user=rdsroot password=K0URYt69-tripo_kafka | master | pgsql | user=rdsroot password=K0URYt69hEUbKSauiPt9 host=tripo-test.c1eakwiuo7nt.us-west-2.rds.amazonaws.com port=5432 dbname=growth sslmode=require | 5432 | tripo_kafka | j0Jgu9bHJLptwXKp1ga6CrMD |  | tripo-dev-service | tripo-growth-core-attribution-mq |  |
| aws-host=tripo-test-rdsroot | master | pgsql | host=tripo-test.c1eakwiuo7nt.us-west-2.rds.amazonaws.com port=5432 user=rdsroot password=K0URYt69hEUbKSauiPt9 dbname=commercial sslmode=require statement_timeout=15000 lock_timeout=5000 | 5432 | rdsroot | K0URYt69hEUbKSauiPt9 | commercial | tripo-dev-service | commercial-postgres |  |

## 不可达集群

| 集群 | 原因 |
| --- | --- |
| bau-dev | 401 Unauthorized |
| de-data-platform | 401 Unauthorized |
