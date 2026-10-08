import urllib.request, urllib.parse, http.cookiejar, json

BASE = "http://archery.itripo3d.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(BASE + "/login/")
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/authenticate/", urllib.parse.urlencode({"username": "admin", "password": "Admin@2026!", "csrfmiddlewaretoken": csrf}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/login/")
opener.open(req)
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "asc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/instance/")
rows = json.loads(opener.open(req).read().decode())["rows"]

# find the 10 by host prefix
targets = ["pgr-2zed6ce237kgpa4f", "pgr-2ze375w5a9sr03xc", "pgr-2zepvvw2n091403q", "pgr-2zem3d4ej1285k1x", "pgm-2zeww8ry8w6a7093", "pgr-2zed88m6g2mmo6k6", "pgr-2ze185ggn528q128", "pgm-2ze39qpz3d26s0j7", "pgm-2ze27afcu2wi905n", "pgm-2ze65e3917t7412a"]
ids = []
for r in rows:
    h = r.get("host", "").lower()
    for t in targets:
        if t in h:
            ids.append(r)
            print("FOUND id=%d name=%s host=%s type=%s" % (r["id"], r["instance_name"], r["host"], r["type"]))
            break

print("\ntotal matched:", len(ids))
id_str = ",".join(str(r["id"]) for r in ids)

# health check
hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + id_str + "&refresh=1").read().decode())
print("\nHEALTH:")
for d in hb.get("rows", []):
    inst = next((r for r in ids if r["id"] == d["id"]), {})
    print("  %s  health=%s  lat=%sms  conn=%s/%s (%s%%)" % (inst.get("instance_name", "?"), d.get("health"), d.get("latency_ms"), d.get("conn"), d.get("conn_max"), d.get("conn_pct")))

# SQL query test on each
print("\nSQL QUERY TEST:")
for r in ids:
    db = "postgres"
    sql = "SELECT 1 AS test"
    data = urllib.parse.urlencode({"instance_name": r["instance_name"], "db_name": db, "schema_name": "public", "sql_content": sql, "limit_num": "10"}).encode()
    req = urllib.request.Request(BASE + "/query/", data, method="POST")
    csrf = next(c.value for c in cj if c.name == "csrftoken")
    req.add_header("X-CSRFToken", csrf)
    req.add_header("Referer", BASE + "/sqlquery/")
    try:
        resp = json.loads(opener.open(req).read().decode())
        if resp.get("status") == 0:
            print("  [OK] %s: query works" % r["instance_name"])
        else:
            print("  [FAIL] %s: %s" % (r["instance_name"], resp.get("msg", "")[:100]))
    except Exception as e:
        print("  [ERR] %s: %s" % (r["instance_name"], str(e)[:80]))
