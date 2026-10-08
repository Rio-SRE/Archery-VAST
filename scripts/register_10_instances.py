#!/usr/bin/env python3
"""Register 10 instances from image, dedup with existing, fix existing, add new, verify."""
import json, re, urllib.request, urllib.parse, http.cookiejar, time

BASE = "http://archery.itripo3d.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(BASE + "/login/")
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/authenticate/", urllib.parse.urlencode({"username": "admin", "password": "Admin@2026!", "csrfmiddlewaretoken": csrf}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf); req.add_header("Referer", BASE + "/login/"); opener.open(req)

# 10 instances from the image
instances = [
    {"rds_id": "pgr-2zed6ce237kgpa4f", "name": "tripo-security-readonly", "ip": "10.128.2.125", "type": "slave", "db_type": "pgsql", "host": "pgr-2zed6ce237kgpa4f.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2zeh3appfem428a3", "master_name": "tripo-security"},
    {"rds_id": "pgr-2ze375w5a9sr03xc", "name": "tripo-idp-readonly", "ip": "10.128.2.123", "type": "slave", "db_type": "pgsql", "host": "pgr-2ze375w5a9sr03xc.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2zev0241m73l2x3s", "master_name": "tripo-idp"},
    {"rds_id": "pgr-2zepvvw2n091403q", "name": "tripo-growth-readonly", "ip": "10.128.2.121", "type": "slave", "db_type": "pgsql", "host": "pgr-2zepvvw2n091403q.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2zefzl63t3s1hx7w", "master_name": "tripo-growth"},
    {"rds_id": "pgr-2zem3d4ej1285k1x", "name": "tripo-app-readonly", "ip": "10.128.2.119", "type": "slave", "db_type": "pgsql", "host": "pgr-2zem3d4ej1285k1x.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2ze3a5y6143le521", "master_name": "tripo-app"},
    {"rds_id": "pgm-2zeww8ry8w6a7093", "name": "tripo-studio", "ip": "10.128.2.113", "type": "master", "db_type": "pgsql", "host": "pgm-2zeww8ry8w6a7093.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "", "master_name": ""},
    {"rds_id": "pgr-2zed88m6g2mmo6k6", "name": "tripo-base-core-user-readonly", "ip": "10.128.2.5", "type": "slave", "db_type": "pgsql", "host": "pgr-2zed88m6g2mmo6k6.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2zez39q8wjad5wjd", "master_name": "tripo-base-core-user"},
    {"rds_id": "pgr-2ze185ggn528q128", "name": "tripo-ux-marketing-readonly", "ip": "10.128.2.250", "type": "slave", "db_type": "pgsql", "host": "pgr-2ze185ggn528q128.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "pgm-2ze39qpz3d26s0j7", "master_name": "tripo-国内运营中台数据库"},
    {"rds_id": "pgm-2ze39qpz3d26s0j7", "name": "tripo-国内运营中台数据库", "ip": "10.128.2.219", "type": "master", "db_type": "pgsql", "host": "pgm-2ze39qpz3d26s0j7.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "", "master_name": ""},
    {"rds_id": "pgm-2ze27afcu2wi905n", "name": "tripo-service-test", "ip": "10.128.2.171", "type": "master", "db_type": "pgsql", "host": "pgm-2ze27afcu2wi905n.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "", "master_name": ""},
    {"rds_id": "pgm-2ze65e3917t7412a", "name": "tripo-commercial", "ip": "10.128.2.96", "type": "master", "db_type": "pgsql", "host": "pgm-2ze65e3917t7412a.pg.rds.aliyuncs.com", "port": 5432, "master_rds": "", "master_name": ""},
]

# default credentials (from ACK secret scan)
CRED_MAP = {
    "pgm-2zeh3appfem428a3": {"user": "tripo", "password": "Tripo3D!Security", "db_name": "tripo_security_tns"},
    "pgm-2zev0241m73l2x3s": {"user": "tripo", "password": "Tripo3D!Idp", "db_name": "tripo_base_idp"},
    "pgm-2zefzl63t3s1hx7w": {"user": "tripo", "password": "Tripo3D!Growth", "db_name": "tripo_growth"},
    "pgm-2ze3a5y6143le521": {"user": "tripo", "password": "Tripo3D!App", "db_name": "tripo_app"},
    "pgm-2zeww8ry8w6a7093": {"user": "tripo", "password": "Tripo3D!AiCoding", "db_name": "litellm"},
    "pgm-2zez39q8wjad5wjd": {"user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "tripo_base_core_user"},
    "pgm-2ze39qpz3d26s0j7": {"user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres"},
    "pgm-2ze27afcu2wi905n": {"user": "monitor", "password": "tAtGOxeBQZA0YmUfJ9Jz994mA1b2", "db_name": "postgres"},
    "pgm-2ze65e3917t7412a": {"user": "alipay_notify_gateway", "password": "0f282775d374aced269e2d15a0aca8b4477ed973754f2404", "db_name": "trade-alipay"},
    "pgr-2zed6ce237kgpa4f": {"user": "tripo", "password": "Tripo3D!Security", "db_name": "tripo_security_tns"},
    "pgr-2ze375w5a9sr03xc": {"user": "tripo", "password": "Tripo3D!Idp", "db_name": "tripo_base_idp"},
    "pgr-2zepvvw2n091403q": {"user": "tripo", "password": "Tripo3D!Growth", "db_name": "tripo_growth"},
    "pgr-2zem3d4ej1285k1x": {"user": "tripo", "password": "Tripo3D!App", "db_name": "tripo_app"},
    "pgr-2zed88m6g2mmo6k6": {"user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "tripo_base_core_user"},
    "pgr-2ze185ggn528q128": {"user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres"},
}

# get existing Archery instances
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "asc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf); req.add_header("Referer", BASE + "/instance/")
existing = json.loads(opener.open(req).read().decode())["rows"]

# build lookup: host -> id, and ip -> id
host_to_id = {}
ip_to_id = {}
for e in existing:
    h = e.get("host", "").lower().strip()
    host_to_id[h] = e["id"]
    if "." in h:
        host_to_id[h.split(".")[0]] = e["id"]
print("Existing:", len(existing))

def get_form_csrf(url):
    resp = opener.open(url, timeout=30)
    page = resp.read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    return m.group(1) if m else None

def admin_save(inst_id, data):
    url = BASE + "/admin/sql/instance/%s/" % (str(inst_id) + "/change" if inst_id else "add")
    if inst_id:
        url = BASE + "/admin/sql/instance/%d/change/" % inst_id
    else:
        url = BASE + "/admin/sql/instance/add/"
    form_csrf = get_form_csrf(url)
    if not form_csrf:
        return "no csrf"
    csrf_cookie = next(c.value for c in cj if c.name == "csrftoken")
    encoded = urllib.parse.urlencode(data, doseq=True).encode()
    req = urllib.request.Request(url, encoded, method="POST")
    req.add_header("Referer", url)
    req.add_header("X-CSRFToken", csrf_cookie)
    try:
        resp = opener.open(req, timeout=30)
        return "OK"
    except urllib.error.HTTPError as e:
        errors = re.findall(r'class="errorlist"[^>]*><li>([^<]+)', e.read().decode())
        return errors or str(e.code)

print("\n=== Processing 10 instances ===")
registered_ids = []
for inst in instances:
    rds_prefix = inst["rds_id"]
    host = inst["host"]
    h_lower = host.lower()
    h_prefix = h_lower.split(".")[0]
    cred = CRED_MAP.get(rds_prefix, {"user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres"})
    # slave uses master's creds
    if inst["type"] == "slave" and inst["master_rds"] in CRED_MAP:
        cred = CRED_MAP[inst["master_rds"]]

    tags = ["1", "5"]  # can_read, aliyun
    if inst["type"] == "master":
        tags = ["1", "2", "5"]  # + can_write

    existing_id = host_to_id.get(h_lower) or host_to_id.get(h_prefix)
    # also check by IP
    for e in existing:
        if e.get("host", "") == inst["ip"]:
            existing_id = e["id"]
            break

    form_data = {
        "instance_name": inst["name"],
        "type": inst["type"],
        "db_type": inst["db_type"],
        "host": host,
        "port": str(inst["port"]),
        "user": cred["user"],
        "password": cred["password"],
        "db_name": cred["db_name"],
        "resource_group": ["1"],
        "instance_tag": tags,
        "_save": "Save",
    }

    if existing_id:
        result = admin_save(existing_id, form_data)
        print("[UPDATE] id=%s %s -> %s" % (existing_id, inst["name"], result))
    else:
        result = admin_save(None, form_data)
        print("[NEW] %s -> %s" % (inst["name"], result))
    time.sleep(0.5)

# verify connectivity
print("\n=== Verifying connectivity ===")
time.sleep(2)
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "desc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf); req.add_header("Referer", BASE + "/instance/")
all_rows = json.loads(opener.open(req).read().decode())["rows"]

check_names = [i["name"] for i in instances]
check_ids = []
for r in all_rows:
    if r["instance_name"] in check_names:
        check_ids.append(str(r["id"]))

if check_ids:
    ids_str = ",".join(check_ids)
    hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + ids_str).read().decode())
    for d in hb.get("rows", []):
        inst_row = next((r for r in all_rows if r["id"] == d["id"]), {})
        name = inst_row.get("instance_name", "?")
        health = d.get("health", "?")
        lat = d.get("latency_ms", "-")
        conn = d.get("conn", 0)
        cpct = d.get("conn_pct", 0)
        print("  %s  health=%s  lat=%sms  conn=%s (%s%%)" % (name, health, lat, conn, cpct))

print("\nDONE")
