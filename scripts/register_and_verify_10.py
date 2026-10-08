#!/usr/bin/env python3
"""
Update 10 existing Archery instances to correct names, hosts (RDS domain),
credentials, tags, and resource_group. Then verify connectivity.
"""
import json, re, urllib.request, urllib.parse, http.cookiejar, time

BASE = "http://archery.itripo3d.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(BASE + "/login/")
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(
    BASE + "/authenticate/",
    urllib.parse.urlencode({
        "username": "admin",
        "password": "Admin@2026!",
        "csrfmiddlewaretoken": csrf,
    }).encode(),
    method="POST",
)
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/login/")
opener.open(req)

UPDATES = [
    {"id": 47, "instance_name": "tripo-security-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2zed6ce237kgpa4f.pg.rds.aliyuncs.com", "port": "5432",
     "user": "tripo", "password": "Tripo3D!Security", "db_name": "tripo_security_tns"},
    {"id": 48, "instance_name": "tripo-idp-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2ze375w5a9sr03xc.pg.rds.aliyuncs.com", "port": "5432",
     "user": "tripo", "password": "Tripo3D!Idp", "db_name": "tripo_base_idp"},
    {"id": 49, "instance_name": "tripo-growth-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2zepvvw2n091403q.pg.rds.aliyuncs.com", "port": "5432",
     "user": "tripo", "password": "Tripo3D!Growth", "db_name": "tripo_growth"},
    {"id": 50, "instance_name": "tripo-app-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2zem3d4ej1285k1x.pg.rds.aliyuncs.com", "port": "5432",
     "user": "tripo", "password": "Tripo3D!App", "db_name": "tripo_app"},
    {"id": 54, "instance_name": "tripo-studio", "type": "master", "db_type": "pgsql",
     "host": "pgm-2zeww8ry8w6a7093.pg.rds.aliyuncs.com", "port": "5432",
     "user": "tripo", "password": "Tripo3D!AiCoding", "db_name": "litellm"},
    {"id": 7, "instance_name": "tripo-base-core-user-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2zed88m6g2mmo6k6.pg.rds.aliyuncs.com", "port": "5432",
     "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "tripo_base_core_user"},
    {"id": 14, "instance_name": "tripo-ux-marketing-readonly", "type": "slave", "db_type": "pgsql",
     "host": "pgr-2ze185ggn528q128.pg.rds.aliyuncs.com", "port": "5432",
     "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres"},
    {"id": 17, "instance_name": "tripo-国内运营中台数据库", "type": "master", "db_type": "pgsql",
     "host": "pgm-2ze39qpz3d26s0j7.pg.rds.aliyuncs.com", "port": "5432",
     "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres"},
    {"id": 23, "instance_name": "tripo-service-test", "type": "master", "db_type": "pgsql",
     "host": "pgm-2ze27afcu2wi905n.pg.rds.aliyuncs.com", "port": "5432",
     "user": "monitor", "password": "tAtGOxeBQZA0YmUfJ9Jz994mA1b2", "db_name": "postgres"},
    {"id": 99, "instance_name": "tripo-commercial", "type": "master", "db_type": "pgsql",
     "host": "pgm-2ze65e3917t7412a.pg.rds.aliyuncs.com", "port": "5432",
     "user": "alipay_notify_gateway", "password": "0f282775d374aced269e2d15a0aca8b4477ed973754f2404",
     "db_name": "trade-alipay"},
]


def get_form_state(url):
    resp = opener.open(url, timeout=30)
    page = resp.read().decode()
    csrf_m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    # extract aliyunrdsconfig inline formset hidden fields
    total = re.search(r'name="aliyunrdsconfig-TOTAL_FORMS"[^>]*value="([^"]*)"', page)
    initial = re.search(r'name="aliyunrdsconfig-INITIAL_FORMS"[^>]*value="([^"]*)"', page)
    min_num = re.search(r'name="aliyunrdsconfig-MIN_NUM_FORMS"[^>]*value="([^"]*)"', page)
    max_num = re.search(r'name="aliyunrdsconfig-MAX_NUM_FORMS"[^>]*value="([^"]*)"', page)
    rds_id_val = re.search(r'name="aliyunrdsconfig-0-id"[^>]*value="([^"]*)"', page)
    rds_inst_val = re.search(r'name="aliyunrdsconfig-0-instance"[^>]*value="([^"]*)"', page)
    rds_dbid_val = re.search(r'name="aliyunrdsconfig-0-rds_dbinstanceid"[^>]*value="([^"]*)"', page)
    return {
        "csrf": csrf_m.group(1) if csrf_m else None,
        "page": page,
        "inline": {
            "TOTAL_FORMS": total.group(1) if total else "1",
            "INITIAL_FORMS": initial.group(1) if initial else "0",
            "MIN_NUM_FORMS": min_num.group(1) if min_num else "0",
            "MAX_NUM_FORMS": max_num.group(1) if max_num else "1",
            "0-id": rds_id_val.group(1) if rds_id_val else "",
            "0-instance": rds_inst_val.group(1) if rds_inst_val else "",
            "0-rds_dbinstanceid": rds_dbid_val.group(1) if rds_dbid_val else "",
        },
    }


print("=== Updating 10 instances via Django admin ===")
for u in UPDATES:
    tags = ["1", "5"]  # can_read + aliyun
    if u["type"] == "master":
        tags = ["1", "2", "5"]  # + can_write

    url = BASE + "/admin/sql/instance/%d/change/" % u["id"]
    state = get_form_state(url)
    if not state["csrf"]:
        print("[FAIL] id=%d %s — no csrf" % (u["id"], u["instance_name"]))
        continue

    csrf_cookie = next(c.value for c in cj if c.name == "csrftoken")
    inline = state["inline"]

    fields = [
        ("csrfmiddlewaretoken", state["csrf"]),
        ("instance_name", u["instance_name"]),
        ("type", u["type"]),
        ("db_type", u["db_type"]),
        ("host", u["host"]),
        ("port", u["port"]),
        ("user", u["user"]),
        ("password", u["password"]),
        ("db_name", u["db_name"]),
        ("资源组", "1"),
    ]
    for t in tags:
        fields.append(("实例标签", t))

    # aliyunrdsconfig inline formset
    fields.append(("aliyunrdsconfig-TOTAL_FORMS", inline["TOTAL_FORMS"]))
    fields.append(("aliyunrdsconfig-INITIAL_FORMS", inline["INITIAL_FORMS"]))
    fields.append(("aliyunrdsconfig-MIN_NUM_FORMS", inline["MIN_NUM_FORMS"]))
    fields.append(("aliyunrdsconfig-MAX_NUM_FORMS", inline["MAX_NUM_FORMS"]))
    fields.append(("aliyunrdsconfig-0-id", inline["0-id"]))
    fields.append(("aliyunrdsconfig-0-instance", inline["0-instance"]))
    fields.append(("aliyunrdsconfig-0-rds_dbinstanceid", inline["0-rds_dbinstanceid"]))
    fields.append(("aliyunrdsconfig-0-ak", ""))
    fields.append(("_save", "保存"))

    encoded = urllib.parse.urlencode(fields, doseq=False).encode()
    req = urllib.request.Request(url, encoded, method="POST")
    req.add_header("Referer", url)
    req.add_header("X-CSRFToken", csrf_cookie)
    try:
        resp = opener.open(req, timeout=30)
        final_url = resp.geturl()
        if "/change/" not in final_url:
            print("[OK]   id=%-4d  %-35s  host=%s" % (u["id"], u["instance_name"], u["host"]))
        else:
            page = resp.read().decode()
            errors = re.findall(r'class="errorlist"[^>]*><li>([^<]+)', page)
            print("[WARN] id=%-4d  %-35s  stayed on form: %s" % (u["id"], u["instance_name"], "; ".join(errors) if errors else "unknown"))
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        errors = re.findall(r'class="errorlist"[^>]*><li>([^<]+)', body)
        print("[FAIL] id=%-4d  %-35s  HTTP %d: %s" % (u["id"], u["instance_name"], e.code, "; ".join(errors) if errors else ""))
    time.sleep(0.3)

# Verify the updates took effect
print("\n=== Verifying updates ===")
time.sleep(1)
for u in UPDATES:
    url = BASE + "/admin/sql/instance/%d/change/" % u["id"]
    resp = opener.open(url, timeout=10)
    page = resp.read().decode()
    name_m = re.search(r'name="instance_name"[^>]*value="([^"]+)"', page)
    host_m = re.search(r'name="host"[^>]*value="([^"]+)"', page)
    name = name_m.group(1) if name_m else "?"
    host = host_m.group(1) if host_m else "?"
    ok = "OK" if name == u["instance_name"] and host == u["host"] else "MISMATCH"
    print("  [%s] id=%-4d  name=%-35s  host=%s" % (ok, u["id"], name, host))

# Health check
print("\n=== Health Check (with refresh) ===")
ids_str = ",".join(str(u["id"]) for u in UPDATES)
hb = json.loads(opener.open(
    BASE + "/instance/health_batch/?ids=" + ids_str + "&refresh=1"
).read().decode())
id_to_name = {u["id"]: u["instance_name"] for u in UPDATES}
for d in hb.get("rows", []):
    name = id_to_name.get(d["id"], "id=%d" % d["id"])
    health = d.get("health", "?")
    lat = d.get("latency_ms", "-")
    conn = d.get("conn", 0)
    conn_max = d.get("conn_max", "-")
    conn_pct = d.get("conn_pct", 0)
    tag = "OK" if health in ("healthy", "up") else "!!"
    print("  [%s] %-35s  health=%-10s  latency=%sms  conn=%s/%s (%s%%)" % (
        tag, name, health, lat, conn, conn_max, conn_pct))

# SQL query test
print("\n=== SQL Query Test (SELECT 1) ===")
for u in UPDATES:
    db = u["db_name"] or "postgres"
    csrf = next(c.value for c in cj if c.name == "csrftoken")
    data = urllib.parse.urlencode({
        "instance_name": u["instance_name"],
        "db_name": db,
        "schema_name": "public",
        "sql_content": "SELECT 1 AS test",
        "limit_num": "10",
    }).encode()
    req = urllib.request.Request(BASE + "/query/", data, method="POST")
    req.add_header("X-CSRFToken", csrf)
    req.add_header("Referer", BASE + "/sqlquery/")
    try:
        resp = json.loads(opener.open(req, timeout=15).read().decode())
        if resp.get("status") == 0:
            print("  [QUERY OK]   %-35s  db=%s" % (u["instance_name"], db))
        else:
            print("  [QUERY FAIL] %-35s  %s" % (u["instance_name"], resp.get("msg", "")[:100]))
    except Exception as e:
        print("  [QUERY ERR]  %-35s  %s" % (u["instance_name"], str(e)[:80]))

print("\n=== DONE ===")
