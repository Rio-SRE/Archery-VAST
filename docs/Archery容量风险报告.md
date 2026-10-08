# Archery 数据库容量风险报告

巡检时间：2026-09-22
巡检范围：全部 91 台实例（阿里云 + AWS）
巡检方式：连接拨测 + 容量水位采集

## 风险总览

| 等级 | 数量 | 说明 |
| --- | --- | --- |
| 严重（水位 ≥80%） | 3 台 | 已超出预估容量，需立即处理 |
| 告警（水位 30-80%） | 2 台 | 水位较高，需关注并评估扩容 |
| 关注（水位 10-30%） | 4 台 | 水位可控，持续观察 |
| 异常（不可达） | 7 台 | 巡检失败，需排查网络/权限 |
| 正常 | 75 台 | 水位健康 |

## 严重风险（水位 ≥80%）

| 实例名称 | HOST | 云 | 角色 | 数据库类型 | 连接水位 | QPS水位 | 建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| global_pg_tripo_core_user | 10.0.54.30 | aws | master | pgsql | 83/512 (16.2%) | 3398.9/1600 (212.4%) | QPS超上限，建议升配或加只读副本分流 |
| tripo_prod_base_user_ops | tripo-prod-base-user-ops.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | aws | master | pgsql | 113/512 (22.1%) | 1852.6/1600 (115.8%) | QPS超上限，建议升配或加只读副本分流 |
| tripo-studio-test | tripo-test.c1eakwiuo7nt.us-west-2.rds.amazonaws.com | aws | master | pgsql | 1130/1024 (110.4%) | 945.5/1600 (59.1%) | 连接数超上限，建议升配或加只读副本分流 |

## 告警风险（水位 30-80%）

| 实例名称 | HOST | 云 | 角色 | 数据库类型 | 连接水位 | QPS水位 | 建议 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tripo-test | pgm-2zecx6rl341ps06d.pg.rds.aliyuncs.com | aliyun | master | pgsql | 299/512 (58.4%) | 72.2/1600 (4.5%) | 连接数水位偏高，投流期间可能触顶，建议提前扩容 |
| bj-pg-vast-tripo-6 | 10.128.2.218 | aliyun | master | pgsql | 349/1024 (34.1%) | 140.4/3200 (4.4%) | 连接数水位偏高，投流期间可能触顶，建议提前扩容 |

## 关注（水位 10-30%）

| 实例名称 | HOST | 云 | 角色 | 数据库类型 | 连接水位 | QPS水位 |
| --- | --- | --- | --- | --- | --- | --- |
| bj-pg-vast-tripo-8 | 10.128.2.201 | aliyun | master | pgsql | 294/1024 (28.7%) | 72.2/1600 (4.5%) |
| bj-pg-vast-tripo-7 | 10.128.2.210 | aliyun | master | pgsql | 91/512 (17.8%) | 16.6/1600 (1.0%) |
| bj-pg-base-core-user | pgm-2zez39q8wjad5wjd.pg.rds.aliyuncs.com | aliyun | master | pgsql | 91/512 (17.8%) | 16.6/1600 (1.0%) |
| tripo_prod_platform_mosaic | tripo-prod-platform-mosaic.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com | aws | master | pgsql | 29/512 (5.7%) | 237.9/1600 (14.9%) |

## 异常实例（巡检不可达）

| 实例名称 | HOST | 云 | 角色 | 数据库类型 | 错误信息 |
| --- | --- | --- | --- | --- | --- |
| algo-inference-mysql | 10.128.2.208 | aliyun | master | mysql | (1040, 'Too many connections') |
| bj-mysql-api-1 | 172.16.0.19 | aliyun | master | mysql | (1040, 'Too many connections') |
| bj-mysql-vast-1 | 10.128.2.208 | aliyun | master | mysql | (1040, 'Too many connections') |
| bj-mysql-vast-2 | 10.128.2.199 | aliyun | master | mysql | (1040, 'Too many connections') |
| bj-mysql-api-2 | 172.16.0.12 | aliyun | master | mysql | (1040, 'Too many connections') |
| aws-api-platform-aegis-test | api-platform-aegis-test.c1eakwiuo7nt.us-west-2.rds.amazonaws.com | aws | master | mysql | (1040, 'Too many connections') |
| aws-superset-db1 | superset-db1.c1eakwiuo7nt.us-west-2.rds.amazonaws.com | aws | master | pgsql | probe timeout |

## 说明

- 连接上限估算：max(50, 内存MB / 8)，按云厂商实例规格
- QPS 上限估算：max(50, CPU核数 × 800)
- 巡检周期：60 秒自动采集，缓存 1 小时
- 数据来源：Archery 实例监控（/instancemonitor/）