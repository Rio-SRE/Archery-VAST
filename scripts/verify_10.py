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

names = ["tripo-security-readonly", "tripo-idp-readonly", "tripo-growth-readonly", "tripo-app-readonly", "tripo-studio", "tripo-base-core-user-readonly", "tripo-ux-marketing-readonly", "tripo-国内运营中台数据库", "tripo-service-test", "tripo-commercial"]

csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "asc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/instance/")
rows = json.loads(opener.open(req).read().decode())["rows"]
ids = []
for r in rows:
    if r["instance_name"] in names:
        ids.append(str(r["id"]))
        print("found", r["id"], r["instance_name"], r["host"], r["type"])
print("ids:", ids)
hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + ",".join(ids) + "&refresh=1").read().decode())
print("batch status:", hb.get("status"), "count:", len(hb.get("rows", [])))
for d in hb.get("rows", []):
    inst = next((r for r in rows if r["id"] == d["id"]), {})
    print("  %s  health=%s  lat=%sms  conn=%s/%s (%s%%)" % (inst.get("instance_name", "?"), d.get("health"), d.get("latency_ms"), d.get("conn"), d.get("conn_max"), d.get("conn_pct")))
