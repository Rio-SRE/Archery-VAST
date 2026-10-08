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

IDS = [7, 14, 17, 23, 45, 47, 48, 49, 50, 54]
NAMES = {
    7: ("tripo-base-core-user-readonly", "slave", "pgr-2zed88m6g2mmo6k6.pg.rds.aliyuncs.com", "guozhenyu", "Wuyu@2026!", "tripo_base_core_user"),
    14: ("tripo-ux-marketing-readonly", "slave", "pgr-2ze185ggn528q128.pg.rds.aliyuncs.com", "guozhenyu", "Wuyu@2026!", "postgres"),
    17: ("tripo-cn-ops-db", "master", "pgm-2ze39qpz3d26s0j7.pg.rds.aliyuncs.com", "guozhenyu", "Wuyu@2026!", "postgres"),
    23: ("tripo-service-test", "master", "pgm-2ze27afcu2wi905n.pg.rds.aliyuncs.com", "monitor", "tAtGOxeBQZA0YmUfJ9Jz994mA1b2", "postgres"),
    45: ("tripo-commercial", "master", "pgm-2ze8z17f8hp2t2be.pg.rds.aliyuncs.com", "tripo", "Tripo3D!AiCoding", "litellm"),
    47: ("tripo-security-readonly", "slave", "pgr-2zed6ce237kgpa4f.pg.rds.aliyuncs.com", "tripo", "Tripo3D!Security", "tripo_security_tns"),
    48: ("tripo-idp-readonly", "slave", "pgr-2ze375w5a9sr03xc.pg.rds.aliyuncs.com", "tripo", "Tripo3D!Idp", "tripo_base_idp"),
    49: ("tripo-growth-readonly", "slave", "pgr-2zepvvw2n091403q.pg.rds.aliyuncs.com", "tripo", "Tripo3D!Growth", "tripo_growth"),
    50: ("tripo-app-readonly", "slave", "pgr-2zem3d4ej1285k1x.pg.rds.aliyuncs.com", "tripo", "Tripo3D!App", "tripo_app"),
    54: ("tripo-studio", "master", "pgm-2zeww8ry8w6a7093.pg.rds.aliyuncs.com", "tripo", "Tripo3D!AiCoding", "litellm"),
}

def get_form_csrf(url):
    resp = opener.open(url, timeout=30)
    page = resp.read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    return m.group(1) if m else None

# Re-save each with resource_group and tags properly set
print("=== Re-saving with resource_group + tags ===")
for iid in IDS:
    name, itype, host, user, pwd, db = NAMES[iid]
    tags = ["1", "5"]  # can_read, aliyun
    if itype == "master":
        tags = ["1", "2", "5"]  # + can_write
    url = BASE + "/admin/sql/instance/%d/change/" % iid
    form_csrf = get_form_csrf(url)
    if not form_csrf:
        print("[FAIL] id=%d no csrf" % iid)
        continue
    csrf_cookie = next(c.value for c in cj if c.name == "csrftoken")
    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": form_csrf,
        "instance_name": name,
        "type": itype,
        "db_type": "pgsql",
        "host": host,
        "port": "5432",
        "user": user,
        "password": pwd,
        "db_name": db,
        "resource_group": ["1"],
        "instance_tag": tags,
        "_save": "Save",
    }, doseq=True).encode()
    req = urllib.request.Request(url, data, method="POST")
    req.add_header("Referer", url)
    req.add_header("X-CSRFToken", csrf_cookie)
    try:
        opener.open(req, timeout=30)
        print("[OK] id=%d %s" % (iid, name))
    except Exception as e:
        print("[FAIL] id=%d %s" % (iid, str(e)[:60]))
    time.sleep(0.3)

# Grant query privileges for admin and dev_lead on all 10
print("\n=== Granting query privileges ===")
for username, display in [("admin", ""), ("dev_lead", "研发负责人")]:
    for iid in IDS:
        name = NAMES[iid][0]
        db = NAMES[iid][5]
        data = urllib.parse.urlencode({
            "instance_name": name,
            "db_name": "*",
            "valid_date": "2099-12-31",
            "limit_num": "10000",
            "priv_type": "1",
        }).encode()
        # Use Archery query privilege API is complex; use DB directly later
        # For now just test if query works after resource_group fix

# Test SQL query
print("\n=== SQL query test ===")
csrf = next(c.value for c in cj if c.name == "csrftoken")
for iid in IDS:
    name, itype, host, user, pwd, db = NAMES[iid]
    qdb = db if db and db != "" else "postgres"
    data = urllib.parse.urlencode({"instance_name": name, "db_name": qdb, "schema_name": "public", "sql_content": "SELECT 1 AS test", "limit_num": "10"}).encode()
    req = urllib.request.Request(BASE + "/query/", data, method="POST")
    req.add_header("X-CSRFToken", csrf)
    req.add_header("Referer", BASE + "/sqlquery/")
    try:
        resp = json.loads(opener.open(req, timeout=15).read().decode())
        if resp.get("status") == 0:
            print("  [OK] %s" % name)
        else:
            print("  [FAIL] %s: %s" % (name, resp.get("msg", "")[:80]))
    except Exception as e:
        print("  [ERR] %s: %s" % (name, str(e)[:60]))

# Health
print("\n=== Health ===")
ids_str = ",".join(str(i) for i in IDS)
hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + ids_str + "&refresh=1").read().decode())
for d in hb.get("rows", []):
    name = NAMES.get(d["id"], ("?",))[0]
    print("  %s  health=%s  lat=%sms  conn=%s/%s (%s%%)" % (name, d.get("health"), d.get("latency_ms"), d.get("conn"), d.get("conn_max"), d.get("conn_pct")))

print("\nDONE")
