#!/bin/bash
# 修复 Archery SQL查询页看不到实例的问题
# 原因: admin 用户未加入资源组的 qs_users
# 使用方法: ssh -i ~/.ssh/cloudpods_key root@39.96.66.171 'bash -s' < scripts/fix_resource_group.sh

cat > /tmp/fix_rg.py << 'PYEOF'
import sys, os
sys.path.insert(0, "/opt/archery")
os.environ["DJANGO_SETTINGS_MODULE"] = "archery.settings"
import django; django.setup()

from django.contrib.auth import get_user_model
from sql.models import Instance, ResourceGroup

User = get_user_model()

# 获取或创建 default 资源组
rg, _ = ResourceGroup.objects.get_or_create(
    group_name="default",
    defaults={"group_id": 1}
)

# 把所有用户加入 default 资源组的 qs_users
for user in User.objects.all():
    rg.users.add(user)
    print("[OK] 用户 %s 已加入 default 资源组" % user.username)

# 确保所有实例关联到 default 资源组
fixed = 0
for inst in Instance.objects.all():
    if not inst.resource_group.filter(pk=rg.pk).exists():
        inst.resource_group.add(rg)
        fixed += 1
        print("[修复] %s 关联到 default 资源组" % inst.instance_name)

print("\n===== 汇总 =====")
print("资源组 default 用户: %s" % list(rg.qs_users.values_list("username", flat=True)))
print("关联实例数: %d / %d" % (Instance.objects.filter(resource_group=rg).count(), Instance.objects.count()))
PYEOF

docker cp /tmp/fix_rg.py archery:/tmp/fix_rg.py
docker exec archery bash -c 'source /opt/venv4archery/bin/activate && cd /opt/archery && python3 /tmp/fix_rg.py'
