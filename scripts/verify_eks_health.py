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
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 20, "offset": 0, "sortName": "id", "sortOrder": "desc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/instance/")
rows = json.loads(opener.open(req).read().decode())["rows"]
new_ids = ",".join(str(r["id"]) for r in rows[:9])
hb = json.loads(opener.open(BASE + "/instance/health_batch/?ids=" + new_ids).read().decode())
for d in hb.get("rows", []):
    inst = next((r for r in rows if r["id"] == d["id"]), {})
    name = inst.get("instance_name", "?")
    h = d.get("health", "?")
    lat = d.get("latency_ms", "-")
    conn = d.get("conn", 0)
    cmax = d.get("conn_max", 0)
    cpct = d.get("conn_pct", 0)
    print("%s  health=%s  lat=%sms  conn=%s/%s (%s%%)" % (name, h, lat, conn, cmax, cpct))
