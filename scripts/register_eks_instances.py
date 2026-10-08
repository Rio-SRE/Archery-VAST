import json, urllib.request, urllib.parse, http.cookiejar, re, time

BASE = "http://archery.itripo3d.com"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open(BASE + "/login/")
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/authenticate/", urllib.parse.urlencode({"username": "admin", "password": "Admin@2026!", "csrfmiddlewaretoken": csrf}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/login/")
opener.open(req)

# get existing hosts to dedup
csrf = next(c.value for c in cj if c.name == "csrftoken")
req = urllib.request.Request(BASE + "/instance/list/", urllib.parse.urlencode({"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "asc", "scope": "all"}).encode(), method="POST")
req.add_header("X-CSRFToken", csrf)
req.add_header("Referer", BASE + "/instance/")
existing = json.loads(opener.open(req).read().decode())["rows"]
existing_hosts = set()
for e in existing:
    h = e.get("host", "").lower().strip()
    existing_hosts.add(h)
    if "." in h:
        existing_hosts.add(h.split(".")[0])
print("existing", len(existing))

instances = [
    {"instance_name": "aws-identities-kratos", "type": "master", "db_type": "pgsql", "host": "identites-main-kratos.proxy-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "kratos", "password": "V0?8Ahju!J6.rvd0pmu:sVfLTubcnV#", "db_name": "kratos"},
    {"instance_name": "aws-litellm-business-relay", "type": "master", "db_type": "pgsql", "host": "litellm-business-relay.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "litellm", "password": "H2a1*qLfB*0Q", "db_name": "litellm"},
    {"instance_name": "aws-tripo-prod-commercial", "type": "master", "db_type": "pgsql", "host": "tripo-prod-commercial.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "tripo_commercial_app", "password": "1df5704ac99531986ec4a66f90ca8a30f6b22240885edb1ecf59c63872970b50", "db_name": "commercial"},
    {"instance_name": "aws-tripo-prod-security", "type": "master", "db_type": "pgsql", "host": "tripo-prod-security.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "rdsroot", "password": "bXL98idKPwHrU7wz", "db_name": "tripo_prod_security"},
    {"instance_name": "aws-tripo-prod-app", "type": "master", "db_type": "pgsql", "host": "tripo-prod-app.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "tripo", "password": "Tripo3D!App", "db_name": "tripo_app"},
    {"instance_name": "aws-database-community", "type": "master", "db_type": "pgsql", "host": "database-community.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "rdsroot", "password": "bXL98idKPwHrU7wz", "db_name": "tripo_community_exp_prod"},
    {"instance_name": "aws-community-task", "type": "master", "db_type": "pgsql", "host": "community-task.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "rdsroot", "password": "bXL98idKPwHrU7wz", "db_name": "tripo_community_task_prod"},
    {"instance_name": "aws-tripo-prod-base-user-rw", "type": "master", "db_type": "pgsql", "host": "tripo-prod-base-user.cluster-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "tripo_base", "password": "Tripo3D!Base", "db_name": "tripo_base_user"},
    {"instance_name": "aws-tripo-prod-base-user-ro", "type": "slave", "db_type": "pgsql", "host": "tripo-prod-base-user.cluster-ro-c1eakwiuo7nt.us-west-2.rds.amazonaws.com", "port": 5432, "user": "tripo_base", "password": "Tripo3D!Base", "db_name": "tripo_base_user"},
]

# dedup against existing
to_register = []
for inst in instances:
    h = inst["host"].lower()
    hp = h.split(".")[0]
    if h in existing_hosts or hp in existing_hosts:
        print("[SKIP]", inst["instance_name"], "already exists")
    else:
        to_register.append(inst)
print("to register:", len(to_register))

def get_form_csrf(url):
    resp = opener.open(url, timeout=30)
    page = resp.read().decode()
    m = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page)
    return m.group(1) if m else None

for inst in to_register:
    tags = ["1", "2", "6"]  # can_read, can_write, aws
    if inst["type"] == "slave":
        tags = ["1", "6"]
    form_csrf = get_form_csrf(BASE + "/admin/sql/instance/add/")
    if not form_csrf:
        print("[FAIL]", inst["instance_name"], "no csrf")
        continue
    csrf_cookie = next(c.value for c in cj if c.name == "csrftoken")
    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": form_csrf,
        "instance_name": inst["instance_name"],
        "type": inst["type"],
        "db_type": inst["db_type"],
        "host": inst["host"],
        "port": str(inst["port"]),
        "user": inst["user"],
        "password": inst["password"],
        "db_name": inst["db_name"],
        "resource_group": ["1"],
        "instance_tag": tags,
        "_save": "Save",
    }, doseq=True).encode()
    req = urllib.request.Request(BASE + "/admin/sql/instance/add/", data, method="POST")
    req.add_header("Referer", BASE + "/admin/sql/instance/add/")
    req.add_header("X-CSRFToken", csrf_cookie)
    try:
        resp = opener.open(req, timeout=30)
        print("[OK]", inst["instance_name"])
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        errors = re.findall(r'class="errorlist"[^>]*><li>([^<]+)', body)
        print("[FAIL]", inst["instance_name"], errors or str(e.code))
    time.sleep(0.5)
