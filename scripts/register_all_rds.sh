#!/bin/bash
# 在阿里云 ECS (39.96.66.171) 上执行此脚本，批量注册/更新所有 RDS 实例到 Archery
# 使用方法: ssh root@39.96.66.171 'bash /tmp/register_all_rds.sh'

cat > /tmp/reg.py << 'PYEOF'
import sys, os
sys.path.insert(0, "/opt/archery")
os.environ["DJANGO_SETTINGS_MODULE"] = "archery.settings"
import django; django.setup()
from sql.models import Instance, ResourceGroup
rg = ResourceGroup.objects.get(group_name="default")

USER = "guozhenyu"
PASSWORD = "Wuyu@2026!"

data = [
    # (实例名, 类型, 地址, 端口)
    # --- PostgreSQL 实例 (端口 5432) ---
    ("bj-pg-algo-data", "pgsql", "10.124.1.126", 5432),
    ("bj-pg-tripo-data", "pgsql", "10.104.18.88", 5432),
    ("bj-pg-vast-tripo-1", "pgsql", "10.128.2.5", 5432),
    ("bj-pg-vast-tripo-2", "pgsql", "10.128.2.251", 5432),
    ("bj-pg-vast-tripo-3", "pgsql", "10.128.2.250", 5432),
    ("bj-pg-algo-inf-1", "pgsql", "10.116.0.187", 5432),
    ("bj-pg-vast-tripo-4", "pgsql", "10.128.2.220", 5432),
    ("bj-pg-vast-tripo-5", "pgsql", "10.128.2.219", 5432),
    ("bj-pg-vast-tripo-6", "pgsql", "10.128.2.218", 5432),
    ("bj-pg-vast-tripo-7", "pgsql", "10.128.2.210", 5432),
    ("bj-pg-vast-tripo-8", "pgsql", "10.128.2.201", 5432),
    ("bj-pg-vast-tripo-9", "pgsql", "10.128.2.171", 5432),
    ("bj-pg-algo-inf-2", "pgsql", "10.116.0.159", 5432),
    ("bj-pg-algo-inf-3", "pgsql", "10.116.0.33", 5432),
    ("bj-pg-algo-inf-4", "pgsql", "10.116.0.32", 5432),
    ("sh-pg-1", "pgsql", "172.31.28.97", 5432),
    ("bj-pg-base-core-user", "pgsql", "pgm-2zez39q8wjad5wjd.pg.rds.aliyuncs.com", 5432),
    # --- MySQL 实例 (端口 3306) ---
    ("bj-mysql-api-1", "mysql", "172.16.0.19", 3306),
    ("bj-mysql-vast-1", "mysql", "10.128.2.208", 3306),
    ("bj-mysql-vast-2", "mysql", "10.128.2.199", 3306),
    ("bj-mysql-api-2", "mysql", "172.16.0.12", 3306),
    ("sh-mysql-1", "mysql", "10.20.133.7", 3306),
    ("aliyun-rds-mysql-1", "mysql", "rm-2ze41f57iqutmybug.mysql.cn-beijing.rds.aliyuncs.com", 3306),
    ("aliyun-rds-mysql-2", "mysql", "rm-2ze3qmtv14hehzh2o.mysql.cn-beijing.rds.aliyuncs.com", 3306),
]

created_count = 0
updated_count = 0

for name, db_type, host, port in data:
    inst, created = Instance.objects.get_or_create(
        instance_name=name,
        defaults={
            "type": "slave",
            "db_type": db_type,
            "host": host,
            "port": port,
            "user": USER,
            "password": PASSWORD,
        }
    )
    if created:
        inst.resource_group.add(rg)
        created_count += 1
        print("[新建] %s (%s %s:%d)" % (name, db_type, host, port))
    else:
        changed = False
        if inst.user != USER:
            inst.user = USER
            changed = True
        if inst.password != PASSWORD:
            inst.password = PASSWORD
            changed = True
        if inst.host != host:
            inst.host = host
            changed = True
        if inst.port != port:
            inst.port = port
            changed = True
        if changed:
            inst.save()
            updated_count += 1
            print("[更新] %s (%s %s:%d)" % (name, db_type, host, port))
        else:
            print("[无变化] %s" % name)
        if not inst.resource_group.filter(pk=rg.pk).exists():
            inst.resource_group.add(rg)

print("\n===== 汇总 =====")
print("新建: %d, 更新: %d, 总计: %d" % (created_count, updated_count, Instance.objects.count()))
PYEOF

docker cp /tmp/reg.py archery:/tmp/reg.py
docker exec archery bash -c 'source /opt/venv4archery/bin/activate && cd /opt/archery && python3 /tmp/reg.py'
