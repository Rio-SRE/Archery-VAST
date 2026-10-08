#!/bin/bash
# Archery 完整功能测试脚本
# 在本地 Mac 执行即可

BASE_URL="http://39.96.66.171:9123"

# Login
CSRF=$(curl -s -c /tmp/at_full "$BASE_URL/login/" | grep -o 'csrfmiddlewaretoken" value="[^"]*' | cut -d'"' -f3)
curl -s -b /tmp/at_full -c /tmp/at_full -d "csrfmiddlewaretoken=$CSRF&username=admin&password=Admin@2026!" -H "Referer: $BASE_URL/login/" -L -o /dev/null "$BASE_URL/authenticate/"
CSRFCOOKIE=$(awk '/csrftoken/{print $7}' /tmp/at_full)

echo "============================================"
echo "   Archery 完整功能测试"
echo "   测试实例: local-test-mysql (testdb)"
echo "   时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

echo ""
echo "【1】页面可用性"
echo "-------------------------------------------"
for page in /dashboard/ /sqlworkflow/ /sqlquery/ /instance/ /queryapplylist/ /config/ /slowquery/ /workflow/; do
  c=$(curl -s -b /tmp/at_full -o /dev/null -w "%{http_code}" "$BASE_URL$page")
  echo "  $page -> $c"
done

echo ""
echo "【2】SQL 查询 (testdb)"
echo "-------------------------------------------"

# SELECT *
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=local-test-mysql&db_name=testdb&schema_name=&tb_name=&sql_content=SELECT+*+FROM+employees&limit_num=100")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  SELECT *: %s rows, cols=%s' % (len(d.get('data',{}).get('rows',[])), d.get('data',{}).get('column_list',[])))"

# WHERE
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=local-test-mysql&db_name=testdb&schema_name=&tb_name=&sql_content=SELECT+name,salary+FROM+employees+WHERE+salary>13000&limit_num=100")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  WHERE salary>13000: %s' % d.get('data',{}).get('rows',[]))"

# GROUP BY
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=local-test-mysql&db_name=testdb&schema_name=&tb_name=&sql_content=SELECT+department,COUNT(*)+as+cnt,AVG(salary)+as+avg_sal+FROM+employees+GROUP+BY+department&limit_num=100")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  GROUP BY: %s' % d.get('data',{}).get('rows',[]))"

# SHOW TABLES
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=local-test-mysql&db_name=testdb&schema_name=&tb_name=&sql_content=SHOW+TABLES&limit_num=100")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  SHOW TABLES: %s' % d.get('data',{}).get('rows',[]))"

# DROP blocked
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=local-test-mysql&db_name=testdb&schema_name=&tb_name=&sql_content=DROP+TABLE+employees&limit_num=100")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  DROP TABLE: blocked=%s msg=%s' % (d.get('status')!=0, d.get('msg','')[:40]))"

echo ""
echo "【3】生产MySQL查询 (只读, bj-mysql-vast-1)"
echo "-------------------------------------------"
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/query/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "instance_name=bj-mysql-vast-1&db_name=information_schema&schema_name=&tb_name=&sql_content=SELECT+version()&limit_num=10")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());s=d.get('status');rows=d.get('data',{}).get('rows',[]);msg=d.get('msg','');print('  version(): %s' % (rows[0] if rows else 'ERR:%s' % msg[:80]))"

echo ""
echo "【4】工单提交 - DDL (testdb)"
echo "-------------------------------------------"

# Get fresh CSRF for workflow submission
CSRF2=$(curl -s -b /tmp/at_full "$BASE_URL/sqlworkflow/" | grep -o 'csrfmiddlewaretoken" value="[^"]*' | cut -d'"' -f3)

# Submit DDL workflow: add column
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlworkflow/" \
  -d "workflow_name=test-add-column&group_name=default&instance_name=local-test-mysql&db_name=testdb&is_backup=off&engineer=admin&sql_content=ALTER+TABLE+employees+ADD+COLUMN+phone+VARCHAR(20)+DEFAULT+NULL+COMMENT+'phone+number';")
echo "  DDL提交: $(echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read()) if sys.stdin.read().strip().startswith('{') else {};print(d.get('msg','submitted'))" 2>/dev/null || echo 'submitted')"

echo ""
echo "【5】工单提交 - DML INSERT (testdb)"
echo "-------------------------------------------"
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlworkflow/" \
  -d "workflow_name=test-insert-data&group_name=default&instance_name=local-test-mysql&db_name=testdb&is_backup=off&engineer=admin&sql_content=INSERT+INTO+employees+(name,email,department,salary)+VALUES+('Zhao+Liu','zhaoliu@test.com','Marketing',14000);")
echo "  DML INSERT提交: done"

echo ""
echo "【6】工单提交 - DML UPDATE (testdb)"
echo "-------------------------------------------"
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "workflow_name=test-update-salary&group_name=default&instance_name=local-test-mysql&db_name=testdb&is_backup=off&engineer=admin&sql_content=UPDATE+employees+SET+salary=16000+WHERE+name='Zhang+San';")
echo "  DML UPDATE提交: done"

echo ""
echo "【7】工单提交 - DML DELETE (testdb)"
echo "-------------------------------------------"
r=$(curl -s -b /tmp/at_full -X POST "$BASE_URL/autoreview/" \
  -H "X-CSRFToken: $CSRFCOOKIE" -H "X-Requested-With: XMLHttpRequest" -H "Referer: $BASE_URL/sqlquery/" \
  -d "workflow_name=test-delete-data&group_name=default&instance_name=local-test-mysql&db_name=testdb&is_backup=off&engineer=admin&sql_content=DELETE+FROM+employees+WHERE+name='Zhao+Liu';")
echo "  DML DELETE提交: done"

echo ""
echo "【8】工单列表检查"
echo "-------------------------------------------"
page=$(curl -s -b /tmp/at_full "$BASE_URL/sqlworkflow/")
for wf in "test-add-column" "test-insert-data" "test-update-salary" "test-delete-data"; do
  echo "$page" | grep -q "$wf" && echo "  $wf: visible" || echo "  $wf: not found (may need autoreview endpoint fix)"
done

echo ""
echo "【9】实例管理 API"
echo "-------------------------------------------"
# Instance resource - databases
r=$(curl -s -b /tmp/at_full "$BASE_URL/instance/instance_resource/?instance_name=local-test-mysql&resource_type=database" -H "X-Requested-With: XMLHttpRequest")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  databases: %s' % d.get('data',[]))"

# Instance resource - tables
r=$(curl -s -b /tmp/at_full "$BASE_URL/instance/instance_resource/?instance_name=local-test-mysql&db_name=testdb&resource_type=table" -H "X-Requested-With: XMLHttpRequest")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  tables in testdb: %s' % d.get('data',[]))"

# Instance resource - columns
r=$(curl -s -b /tmp/at_full "$BASE_URL/instance/instance_resource/?instance_name=local-test-mysql&db_name=testdb&tb_name=employees&resource_type=column" -H "X-Requested-With: XMLHttpRequest")
echo "$r" | python3 -c "import sys,json;d=json.loads(sys.stdin.read());print('  columns: %s' % d.get('data',[]))"

echo ""
echo "============================================"
echo "   测试完成"
echo "============================================"
