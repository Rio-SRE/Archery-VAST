import urllib.request, urllib.parse, http.cookiejar, json, re, time

BASE = "http://archery.itripo3d.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(BASE + "/login/")
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/authenticate/", urllib.parse.urlencode({"username": "admin", "password": "Admin@2026!", "csrfmiddlewaretoken": csrf}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/login/")
opener.open(req)

updates = [
    {"id": 47, "instance_name": "tripo-security-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2zed6ce237kgpa4f.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!Security", "db_name": "tripo_security_tns", "tags": ["1", "5"]},
    {"id": 48, "instance_name": "tripo-idp-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2ze375w5a9sr03xc.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!Idp", "db_name": "tripo_base_idp", "tags": ["1", "5"]},
    {"id": 49, "instance_name": "tripo-growth-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2zepvvw2n091403q.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!Growth", "db_name": "tripo_growth", "tags": ["1", "5"]},
    {"id": 50, "instance_name": "tripo-app-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2zem3d4ej1285k1x.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!App", "db_name": "tripo_app", "tags": ["1", "5"]},
    {"id": 54, "instance_name": "tripo-studio", "type": "master", "db_type": "pgsql", "host": "pgm-2zeww8ry8w6a7093.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!AiCoding", "db_name": "litellm", "tags": ["1", "2", "5"]},
    {"id": 7, "instance_name": "tripo-base-core-user-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2zed88m6g2mmo6k6.pg.rds.aliyuncs.com", "port": "5432", "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "tripo_base_core_user", "tags": ["1", "5"]},
    {"id": 14, "instance_name": "tripo-ux-marketing-readonly", "type": "slave", "db_type": "pgsql", "host": "pgr-2ze185ggn528q128.pg.rds.aliyuncs.com", "port": "5432", "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres", "tags": ["1", "5"]},
    {"id": 17, "instance_name": "tripo-cn-ops-db", "type": "master", "db_type": "pgsql", "host": "pgm-2ze39qpz3d26s0j7.pg.rds.aliyuncs.com", "port": "5432", "user": "guozhenyu", "password": "Wuyu@2026!", "db_name": "postgres", "tags": ["1", "2", "5"]},
    {"id": 23, "instance_name": "tripo-service-test", "type": "master", "db_type": "pgsql", "host": "pgm-2ze27afcu2wi905n.pg.rds.aliyuncs.com", "port": "5432", "user": "monitor", "password": "tAtGOxeBQZA0YmUfJ9Jz994mA1b2", "db_name": "postgres", "tags": ["1", "2", "5"]},
    {"id": 45, "instance_name": "tripo-commercial", "type": "master", "db_type": "pgsql", "host": "pgm-2ze8z17f8hp2t2be.pg.rds.aliyuncs.com", "port": "5432", "user": "tripo", "password": "Tripo3D!AiCoding", "db_name": "litellm", "tags": ["1", "2", "5"]},
]

def get_form_csrf(url):
    resp = opener.open(url, timeout=30)
    page = resp.read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    return m.group(1) if m else None

print("=== Updating 10 instances ===")
for u in updates:
    url = BASE + "/admin/sql/instance/%d/change/" % u["id"]
    form_csrf = get_form_csrf(url)
    if not form_csrf:
        print("[FAIL] id=%d %s no csrf" % (u["id"], u["instance_name"]))
        continue
    csrf_cookie = next(c.value for c in cj if c.name == "csrftoken")
    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": form_csrf,
        "instance_name": u["instance_name"],
        "type": u["type"],
        "db_type": u["db_type"],
        "host": u["host"],
        "port": u["port"],
        "user": u["user"],
        "password": u["password"],
        "db_name": u["db_name"],
        "resource_group": ["1"],
        "instance_tag": u["tags"],
        "_save": "Save",
    }, doseq=True).encode()
    req = urllib.request.Request(url, data, method="POST")
    req.add_header("Referer", url)
    req.add_header("X-CSRFToken", csrf_cookie)
    try:
        resp = opener.open(req, timeout=30)
        print("[OK] id=%d %s -> %s" % (u["id"], u["instance_name"], u["host"]))
    except Exception as e:
        print("[FAIL] id=%d %s %s" % (u["id"], u["instance_name"], str(e)[:80]))
    time.sleep(0.3)

# Verify
print("\n=== Health check ===")
ids_str = ",".join(str(u["id"]) for u in updates)
time.sleep(2)
hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + ids_str + "&refresh=1").read().decode())
for d in hb.get("rows", []):
    name = next((u["instance_name"] for u in updates if u["id"] == d["id"]), "?")
    print("  %s  health=%s  lat=%sms  conn=%s/%s (%s%%)" % (name, d.get("health"), d.get("latency_ms"), d.get("conn"), d.get("conn_max"), d.get("conn_pct")))

# SQL query test
print("\n=== SQL query test ===")
csrf = next(c.value for c in cj if c.name == "csrftoken")
for u in updates:
    data = urllib.parse.urlencode({"instance_name": u["instance_name"], "db_name": u["db_name"] or "postgres", "schema_name": "public", "sql_content": "SELECT 1 AS test", "limit_num": "10"}).encode()
    req = urllib.request.Request(BASE + "/query/", data, method="POST")
    req.add_header("X-CSRFToken", csrf)
    req.add_header("Referer", BASE + "/sqlquery/")
    try:
        resp = json.loads(opener.open(req, timeout=15).read().decode())
        if resp.get("status") == 0:
            print("  [QUERY OK] %s" % u["instance_name"])
        else:
            print("  [QUERY FAIL] %s: %s" % (u["instance_name"], resp.get("msg", "")[:80]))
    except Exception as e:
        print("  [QUERY ERR] %s: %s" % (u["instance_name"], str(e)[:60]))

print("\nDONE")
