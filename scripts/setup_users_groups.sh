#!/bin/bash
# 在阿里云 ECS (39.96.66.171) 上执行此脚本，创建权限组、资源组和用户
# 使用方法: ssh root@39.96.66.171 'bash /tmp/setup_users_groups.sh'

cat > /tmp/setup_users_groups.py << 'PYEOF'
import sys, os
sys.path.insert(0, "/opt/archery")
os.environ["DJANGO_SETTINGS_MODULE"] = "archery.settings"
import django; django.setup()

from django.contrib.auth.models import User, Group, Permission
from sql.models import ResourceGroup

print("=" * 50)
print("Archery 权限分组与用户初始化")
print("=" * 50)

# ============================================================
# 1. 创建权限组 (Django auth.Group)
# ============================================================
print("\n[1/4] 创建权限组...")

groups_config = {
    "DBA": "数据库管理员 - SQL审核/工单审批/实例管理",
    "Dev-Lead": "研发负责人 - 工单一级审核",
    "Developer": "普通研发 - 提交工单/SQL查询/权限申请",
    "QA": "测试人员 - SQL查询(只读)/权限申请",
}

for name, desc in groups_config.items():
    grp, created = Group.objects.get_or_create(name=name)
    status = "创建" if created else "已存在"
    print(f"  [{status}] 权限组: {name} ({desc})")

# ============================================================
# 2. 创建资源组 (ResourceGroup)
# ============================================================
print("\n[2/4] 创建资源组...")

resource_groups_config = {
    "default": "公共/测试实例",
    "production": "生产环境实例",
    "staging": "预发/测试环境实例",
}

rg_objs = {}
for name, desc in resource_groups_config.items():
    rg, created = ResourceGroup.objects.get_or_create(
        group_name=name,
        defaults={"group_id": ResourceGroup.objects.count() + 1}
    )
    rg_objs[name] = rg
    status = "创建" if created else "已存在"
    print(f"  [{status}] 资源组: {name} ({desc})")

# ============================================================
# 3. 创建用户并分配权限组和资源组
# ============================================================
print("\n[3/4] 创建用户...")

users_config = [
    {
        "username": "dba1",
        "password": "Dba1@2026!",
        "display": "DBA-张三",
        "email": "dba1@company.com",
        "is_superuser": False,
        "groups": ["DBA"],
        "resource_groups": ["production", "staging"],
    },
    {
        "username": "dev_lead",
        "password": "LeadDev#2026!Secure",
        "display": "研发负责人",
        "email": "devlead@company.com",
        "is_superuser": False,
        "groups": ["Dev-Lead"],
        "resource_groups": ["default", "staging"],
    },
    {
        "username": "dev1",
        "password": "Dev1@2026!",
        "display": "开发-李四",
        "email": "dev1@company.com",
        "is_superuser": False,
        "groups": ["Developer"],
        "resource_groups": ["default", "staging"],
    },
    {
        "username": "dev2",
        "password": "Dev2@2026!",
        "display": "开发-王五",
        "email": "dev2@company.com",
        "is_superuser": False,
        "groups": ["Developer"],
        "resource_groups": ["default", "staging"],
    },
    {
        "username": "qa1",
        "password": "Qa1@2026!",
        "display": "测试-赵六",
        "email": "qa1@company.com",
        "is_superuser": False,
        "groups": ["QA"],
        "resource_groups": ["default", "staging"],
    },
]

for u in users_config:
    user, created = User.objects.get_or_create(
        username=u["username"],
        defaults={
            "email": u["email"],
            "is_active": True,
            "is_superuser": u["is_superuser"],
        }
    )
    if created:
        user.set_password(u["password"])
        user.first_name = u["display"]
        user.save()
        print(f"  [创建] 用户: {u['username']} ({u['display']})")
    else:
        print(f"  [已存在] 用户: {u['username']} ({u['display']})")

    # 分配权限组
    for gname in u["groups"]:
        grp = Group.objects.get(name=gname)
        user.groups.add(grp)

    # 分配资源组
    for rgname in u["resource_groups"]:
        rg_objs[rgname].qs_users.add(user)

# 确保 admin 加入所有资源组
admin_user = User.objects.get(username="admin")
for rg in rg_objs.values():
    rg.qs_users.add(admin_user)
print(f"  [更新] admin 已加入所有资源组")

# ============================================================
# 4. 配置审批流 (WorkflowAudit 相关)
# ============================================================
print("\n[4/4] 配置审批流...")

from sql.models import WorkflowAuditSetting

# SQL上线审批流: Dev-Lead -> DBA (两级审批)
dev_lead_group = Group.objects.get(name="Dev-Lead")
dba_group = Group.objects.get(name="DBA")

# workflow_type=2 是 SQL上线, 仅 Dev-Lead 审批
audit_setting, created = WorkflowAuditSetting.objects.get_or_create(
    workflow_type=2,
    defaults={
        "group_id": dev_lead_group.id,
        "audit_auth_groups": f"{dev_lead_group.id}",
    }
)
if not created:
    audit_setting.audit_auth_groups = f"{dev_lead_group.id}"
    audit_setting.save()
    print(f"  [更新] SQL上线审批流: Dev-Lead 审核")
else:
    print(f"  [创建] SQL上线审批流: Dev-Lead 审核")

# workflow_type=1 是查询权限, 无需审批 (删除已有记录)
deleted_count, _ = WorkflowAuditSetting.objects.filter(workflow_type=1).delete()
if deleted_count:
    print(f"  [删除] 查询权限审批流: 已清除 {deleted_count} 条记录, 无需审批")
else:
    print(f"  [无需操作] 查询权限审批流: 无审批记录, 自动授权")

# ============================================================
# 汇总
# ============================================================
print("\n" + "=" * 50)
print("初始化完成！账号汇总：")
print("=" * 50)
print(f"{'用户名':<12} {'密码':<16} {'角色':<12} {'资源组'}")
print("-" * 60)
print(f"{'admin':<12} {'Admin@2026!':<16} {'DBA(超管)':<12} {'all'}")
for u in users_config:
    print(f"{u['username']:<12} {u['password']:<16} {','.join(u['groups']):<12} {','.join(u['resource_groups'])}")
print(f"{'developer':<12} {'Dev@2026!':<16} {'Developer':<12} {'default'}")
print("-" * 60)
print("审批流:")
print("  SQL上线: 提交 → Dev-Lead审核 → 执行")
print("  查询权限: 无需审批, 自动授权")
print("=" * 50)
PYEOF

docker cp /tmp/setup_users_groups.py archery:/tmp/setup_users_groups.py
docker exec archery bash -c 'source /opt/venv4archery/bin/activate && cd /opt/archery && python3 /tmp/setup_users_groups.py'
