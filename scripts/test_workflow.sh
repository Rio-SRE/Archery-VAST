#!/bin/bash
# 工单提交测试 - 用正确的参数格式
BASE_URL="http://39.96.66.171:9123"

# Login
CSRF=$(curl -s -c /tmp/at_wf "$BASE_URL/login/" | grep -o 'csrfmiddlewaretoken" value="[^"]*' | cut -d'"' -f3)
curl -s -b /tmp/at_wf -c /tmp/at_wf -d "csrfmiddlewaretoken=$CSRF&username=admin&password=Admin@2026!" -H "Referer: $BASE_URL/login/" -L -o /dev/null "$BASE_URL/authenticate/"
CSRFCOOKIE=$(awk '/csrftoken/{print $7}' /tmp/at_wf)

echo "=== 工单提交测试 ==="
echo ""

# 提交 DDL 工单 (用 group_id=1 而不是 group_name)
echo "[1] 提交 DDL 工单: ALTER TABLE employees ADD COLUMN phone"
r=$(curl -s -b /tmp/at_wf -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Referer: $BASE_URL/simsubmit/" \
  -d "workflow_name=test-ddl-add-phone&group_id=1&instance_name=local-test-mysql&db_name=testdb&is_backup=False&engineer=admin&sql_content=ALTER+TABLE+employees+ADD+COLUMN+phone+VARCHAR(20)+DEFAULT+NULL;")
echo "  Response: $(echo "$r" | python3 -c "import sys,json;data=sys.stdin.read();
try:
    d=json.loads(data);print('status=%s msg=%s' % (d.get('status'),d.get('msg','')))
except:
    print('HTML page returned (len=%d)' % len(data))" 2>/dev/null)"

echo ""
echo "[2] 提交 DML INSERT 工单"
r=$(curl -s -b /tmp/at_wf -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Referer: $BASE_URL/simsubmit/" \
  -d "workflow_name=test-dml-insert&group_id=1&instance_name=local-test-mysql&db_name=testdb&is_backup=False&engineer=admin&sql_content=INSERT+INTO+employees+(name,email,department,salary)+VALUES+('Zhao+Liu','zhaoliu@test.com','Marketing',14000);")
echo "  Response: $(echo "$r" | python3 -c "import sys,json;data=sys.stdin.read();
try:
    d=json.loads(data);print('status=%s msg=%s' % (d.get('status'),d.get('msg','')))
except:
    print('HTML page returned (len=%d)' % len(data))" 2>/dev/null)"

echo ""
echo "[3] 提交 DML UPDATE 工单"
r=$(curl -s -b /tmp/at_wf -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Referer: $BASE_URL/simsubmit/" \
  -d "workflow_name=test-dml-update&group_id=1&instance_name=local-test-mysql&db_name=testdb&is_backup=False&engineer=admin&sql_content=UPDATE+employees+SET+salary=16000+WHERE+name='Zhang+San';")
echo "  Response: $(echo "$r" | python3 -c "import sys,json;data=sys.stdin.read();
try:
    d=json.loads(data);print('status=%s msg=%s' % (d.get('status'),d.get('msg','')))
except:
    print('HTML page returned (len=%d)' % len(data))" 2>/dev/null)"

echo ""
echo "[4] 提交 DML DELETE 工单"
r=$(curl -s -b /tmp/at_wf -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" \
  -H "X-Requested-With: XMLHttpRequest" \
  -H "Referer: $BASE_URL/simsubmit/" \
  -d "workflow_name=test-dml-delete&group_id=1&instance_name=local-test-mysql&db_name=testdb&is_backup=False&engineer=admin&sql_content=DELETE+FROM+employees+WHERE+name='Zhao+Liu';")
echo "  Response: $(echo "$r" | python3 -c "import sys,json;data=sys.stdin.read();
try:
    d=json.loads(data);print('status=%s msg=%s' % (d.get('status'),d.get('msg','')))
except:
    print('HTML page returned (len=%d)' % len(data))" 2>/dev/null)"

echo ""
echo "[5] 检查工单列表"
page=$(curl -s -b /tmp/at_wf "$BASE_URL/sqlworkflow/")
for wf in "test-ddl-add-phone" "test-dml-insert" "test-dml-update" "test-dml-delete"; do
  echo "$page" | grep -q "$wf" && echo "  $wf: ✅ visible" || echo "  $wf: ❌ not found"
done

echo ""
echo "[6] 审批第一个工单 (如果存在)"
# 找工单ID
wf_id=$(echo "$page" | grep -oP 'detail/\K[0-9]+' | head -1)
if [ -n "$wf_id" ]; then
  echo "  Found workflow id=$wf_id, approving..."
  r=$(curl -s -b /tmp/at_wf -X POST "$BASE_URL/passed/" \
    -H "X-CSRFToken: $CSRFCOOKIE" \
    -H "Referer: $BASE_URL/detail/$wf_id/" \
    -d "csrfmiddlewaretoken=$CSRFCOOKIE&workflow_id=$wf_id&audit_remark=test+approved" \
    -o /dev/null -w "%{http_code}")
  echo "  Approve HTTP: $r"
  # Check status after approval
  detail=$(curl -s -b /tmp/at_wf "$BASE_URL/detail/$wf_id/")
  echo "$detail" | grep -oE "workflow_review_pass|workflow_finish|workflow_manreviewing" | head -1 | xargs -I{} echo "  Status: {}"
else
  echo "  No workflows found to approve"
fi

echo ""
echo "=== 工单测试完成 ==="
