# -*- coding: UTF-8 -*-

import MySQLdb
import os
import time
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections
from django_redis import get_redis_connection

import simplejson as json
from django.conf import settings
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.views.decorators.cache import cache_page

from common.utils.extend_json_encoder import ExtendJSONEncoder
from common.utils.convert import Convert
from sql.engines import get_engine
from sql.plugins.schemasync import SchemaSync
from sql.utils.sql_utils import filter_db_list
from .models import Instance, ParamTemplate, ParamHistory


@permission_required("sql.menu_instance_list", raise_exception=True)
def lists(request):
    """获取实例列表"""
    limit = int(request.POST.get("limit"))
    offset = int(request.POST.get("offset"))
    type = request.POST.get("type")
    db_type = request.POST.get("db_type")
    tags = request.POST.getlist("tags[]")
    limit = offset + limit
    search = request.POST.get("search", "")
    sortName = request.POST.get("sortName", "instance_name")
    sortOrder = (request.POST.get("sortOrder") or "asc").lower()

    # 组合筛选项
    filter_dict = dict()
    # 过滤搜索
    if search:
        filter_dict["instance_name__icontains"] = search
    # 过滤实例类型
    if type:
        filter_dict["type"] = type
    # 过滤数据库类型
    if db_type:
        filter_dict["db_type"] = db_type

    instances = Instance.objects.filter(**filter_dict)
    scope = request.POST.get("scope") or request.GET.get("scope") or "manual"
    if scope == "manual":
        instances = instances.exclude(instance_tag__tag_code="imported")
    elif scope == "imported":
        instances = instances.filter(instance_tag__tag_code="imported")
    # 过滤标签，返回同时包含全部标签的实例，TODO 循环会生成多表JOIN，如果数据量大会存在效率问题
    if tags:
        for tag in tags:
            instances = instances.filter(instance_tag=tag, instance_tag__active=True)

    count = instances.count()
    allowed_sort = {"id", "instance_name", "db_type", "type", "host", "port", "user"}
    if sortName not in allowed_sort:
        sortName = "id"
    if sortName == "instance_name":
        instances = instances.order_by(getattr(Convert(sortName, "gbk"), sortOrder)())
    else:
        instances = instances.order_by(
            "-" + sortName if sortOrder == "desc" else sortName
        )
    instances = instances.prefetch_related("instance_tag")[offset:limit]

    # QuerySet 序列化
    rows = []
    for inst in instances:
        tags = list(inst.instance_tag.filter(active=True).values_list("tag_code", flat=True))
        if "aws" in tags:
            cloud = "aws"
        elif "aliyun" in tags:
            cloud = "aliyun"
        else:
            host = (inst.host or "").lower()
            if "amazonaws.com" in host or host.startswith("10.0."):
                cloud = "aws"
            elif "aliyuncs.com" in host:
                cloud = "aliyun"
            else:
                cloud = "aliyun"
        rows.append({
            "id": inst.id,
            "instance_name": inst.instance_name,
            "db_type": inst.db_type,
            "type": inst.type,
            "host": inst.host,
            "port": inst.port,
            "user": inst.user,
            "cloud": cloud,
        })

    result = {"total": count, "rows": rows}
    return HttpResponse(
        json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
        content_type="application/json",
    )


@permission_required("sql.param_view", raise_exception=True)
def param_list(request):
    """
    获取实例参数列表
    :param request:
    :return:
    """
    instance_id = request.POST.get("instance_id")
    editable = True if request.POST.get("editable") else False
    search = request.POST.get("search", "")
    try:
        ins = Instance.objects.get(id=instance_id)
    except Instance.DoesNotExist:
        result = {"status": 1, "msg": "实例不存在", "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")
    # 获取已配置参数列表
    cnf_params = dict()
    for param in ParamTemplate.objects.filter(
        db_type=ins.db_type, variable_name__contains=search
    ).values(
        "id",
        "variable_name",
        "default_value",
        "valid_values",
        "description",
        "editable",
    ):
        param["variable_name"] = param["variable_name"].lower()
        cnf_params[param["variable_name"]] = param
    # 获取实例参数列表
    engine = get_engine(instance=ins)
    ins_variables = engine.get_variables()
    # 处理结果
    rows = list()
    for variable in ins_variables.rows:
        variable_name = variable[0].lower()
        row = {
            "variable_name": variable_name,
            "runtime_value": variable[1],
            "editable": False,
        }
        if variable_name in cnf_params.keys():
            row = dict(row, **cnf_params[variable_name])
        rows.append(row)
    # 过滤参数
    if editable:
        rows = [row for row in rows if row["editable"]]
    else:
        rows = [row for row in rows if not row["editable"]]
    return HttpResponse(
        json.dumps(rows, cls=ExtendJSONEncoder, bigint_as_string=True),
        content_type="application/json",
    )


@permission_required("sql.param_view", raise_exception=True)
def param_history(request):
    """实例参数修改历史"""
    limit = int(request.POST.get("limit"))
    offset = int(request.POST.get("offset"))
    limit = offset + limit
    instance_id = request.POST.get("instance_id")
    search = request.POST.get("search", "")
    phs = ParamHistory.objects.filter(instance__id=instance_id)
    # 过滤搜索条件
    if search:
        phs = ParamHistory.objects.filter(variable_name__contains=search)
    count = phs.count()
    phs = phs[offset:limit].values(
        "instance__instance_name",
        "variable_name",
        "old_var",
        "new_var",
        "user_display",
        "create_time",
    )
    # QuerySet 序列化
    rows = [row for row in phs]

    result = {"total": count, "rows": rows}
    return HttpResponse(
        json.dumps(result, cls=ExtendJSONEncoder, bigint_as_string=True),
        content_type="application/json",
    )


@permission_required("sql.param_edit", raise_exception=True)
def param_edit(request):
    user = request.user
    instance_id = request.POST.get("instance_id")
    variable_name = request.POST.get("variable_name")
    variable_value = request.POST.get("runtime_value")
    try:
        ins = Instance.objects.get(id=instance_id)
    except Instance.DoesNotExist:
        result = {"status": 1, "msg": "实例不存在", "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")

    # 修改参数
    engine = get_engine(instance=ins)
    variable_name = engine.escape_string(variable_name)
    variable_value = engine.escape_string(variable_value)
    # 校验是否配置模板
    if not ParamTemplate.objects.filter(variable_name=variable_name).exists():
        result = {"status": 1, "msg": "请先在参数模板中配置该参数！", "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")
    # 获取当前运行参数值
    runtime_value = engine.get_variables(variables=[variable_name]).rows[0][1]
    if variable_value == runtime_value:
        result = {"status": 1, "msg": "参数值与实际运行值一致，未调整！", "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")
    set_result = engine.set_variable(
        variable_name=variable_name, variable_value=variable_value
    )
    if set_result.error:
        result = {
            "status": 1,
            "msg": f"设置错误，错误信息：{set_result.error}",
            "data": [],
        }
        return HttpResponse(json.dumps(result), content_type="application/json")
    # 修改成功的保存修改记录
    else:
        ParamHistory.objects.create(
            instance=ins,
            variable_name=variable_name,
            old_var=runtime_value,
            new_var=variable_value,
            set_sql=set_result.full_sql,
            user_name=user.username,
            user_display=user.display,
        )
        result = {"status": 0, "msg": "修改成功，请手动持久化到配置文件！", "data": []}
    return HttpResponse(json.dumps(result), content_type="application/json")


@permission_required("sql.menu_schemasync", raise_exception=True)
def schemasync(request):
    """对比实例schema信息"""
    instance_name = request.POST.get("instance_name")
    db_name = request.POST.get("db_name")
    target_instance_name = request.POST.get("target_instance_name")
    target_db_name = request.POST.get("target_db_name")
    sync_auto_inc = True if request.POST.get("sync_auto_inc") == "true" else False
    sync_comments = True if request.POST.get("sync_comments") == "true" else False
    result = {
        "status": 0,
        "msg": "ok",
        "data": {"diff_stdout": "", "patch_stdout": "", "revert_stdout": ""},
    }

    # 循环对比全部数据库
    if db_name == "all" or target_db_name == "all":
        db_name = "*"
        target_db_name = "*"

    # 取出该实例的连接方式
    instance = Instance.objects.get(instance_name=instance_name)
    target_instance = Instance.objects.get(instance_name=target_instance_name)

    # 提交给SchemaSync获取对比结果
    schema_sync = SchemaSync()
    # 准备参数
    tag = int(time.time())
    output_directory = os.path.join(settings.BASE_DIR, "downloads/schemasync/")
    os.makedirs(output_directory, exist_ok=True)

    username, password = instance.get_username_password()
    target_username, target_password = target_instance.get_username_password()

    args = {
        "sync-auto-inc": sync_auto_inc,
        "sync-comments": sync_comments,
        "charset": "utf8mb4",
        "tag": tag,
        "output-directory": output_directory,
        "source": f"mysql://{username}:{password}@{instance.host}:{instance.port}/{db_name}",
        "target": f"mysql://{target_username}:{target_password}@{target_instance.host}:{target_instance.port}/{target_db_name}",
    }
    # 参数检查
    args_check_result = schema_sync.check_args(args)
    if args_check_result["status"] == 1:
        return HttpResponse(
            json.dumps(args_check_result), content_type="application/json"
        )
    # 参数转换
    cmd_args = schema_sync.generate_args2cmd(args)
    # 执行命令
    try:
        stdout, stderr = schema_sync.execute_cmd(cmd_args).communicate()
        diff_stdout = f"{stdout}{stderr}"
    except RuntimeError as e:
        diff_stdout = str(e)

    # 非全部数据库对比可以读取对比结果并在前端展示
    if db_name != "*":
        date = time.strftime("%Y%m%d", time.localtime())
        patch_sql_file = "%s%s_%s.%s.patch.sql" % (
            output_directory,
            target_db_name,
            tag,
            date,
        )
        revert_sql_file = "%s%s_%s.%s.revert.sql" % (
            output_directory,
            target_db_name,
            tag,
            date,
        )
        try:
            with open(patch_sql_file, "r") as f:
                patch_sql = f.read()
        except FileNotFoundError as e:
            patch_sql = str(e)
        try:
            with open(revert_sql_file, "r") as f:
                revert_sql = f.read()
        except FileNotFoundError as e:
            revert_sql = str(e)
        result["data"] = {
            "diff_stdout": diff_stdout,
            "patch_stdout": patch_sql,
            "revert_stdout": revert_sql,
        }
    else:
        result["data"] = {
            "diff_stdout": diff_stdout,
            "patch_stdout": "",
            "revert_stdout": "",
        }

    return HttpResponse(json.dumps(result), content_type="application/json")


@cache_page(60 * 5, key_prefix="insRes")
def instance_resource(request):
    """
    获取实例内的资源信息，database、schema、table、column
    :param request:
    :return:
    """
    instance_id = request.GET.get("instance_id")
    instance_name = request.GET.get("instance_name")
    db_name = request.GET.get("db_name", "")
    schema_name = request.GET.get("schema_name", "")
    tb_name = request.GET.get("tb_name", "")

    resource_type = request.GET.get("resource_type")
    if instance_id:
        instance = Instance.objects.get(id=instance_id)
    else:
        try:
            instance = Instance.objects.get(instance_name=instance_name)
        except Instance.DoesNotExist:
            result = {"status": 1, "msg": "实例不存在", "data": []}
            return HttpResponse(json.dumps(result), content_type="application/json")
    result = {"status": 0, "msg": "ok", "data": []}

    try:
        query_engine = get_engine(instance=instance)
        db_name = query_engine.escape_string(db_name)
        schema_name = query_engine.escape_string(schema_name)
        tb_name = query_engine.escape_string(tb_name)
        if resource_type == "database":
            resource = query_engine.get_all_databases()
            resource.rows = filter_db_list(
                db_list=resource.rows,
                db_name_regex=query_engine.instance.show_db_name_regex,
                is_match_regex=True,
            )
            resource.rows = filter_db_list(
                db_list=resource.rows,
                db_name_regex=query_engine.instance.denied_db_name_regex,
                is_match_regex=False,
            )
        elif resource_type == "schema" and db_name:
            resource = query_engine.get_all_schemas(db_name=db_name)
        elif resource_type == "table" and db_name:
            resource = query_engine.get_all_tables(
                db_name=db_name, schema_name=schema_name
            )
        elif resource_type == "column" and db_name and tb_name:
            resource = query_engine.get_all_columns_by_tb(
                db_name=db_name, tb_name=tb_name, schema_name=schema_name
            )
        else:
            raise TypeError("不支持的资源类型或者参数不完整！")
    except Exception as msg:
        result["status"] = 1
        result["msg"] = str(msg)
    else:
        if resource.error:
            result["status"] = 1
            result["msg"] = resource.error
        else:
            result["data"] = resource.rows
    return HttpResponse(json.dumps(result), content_type="application/json")


def describe(request):
    """获取表结构"""
    instance_name = request.POST.get("instance_name")
    try:
        instance = Instance.objects.get(instance_name=instance_name)
    except Instance.DoesNotExist:
        result = {"status": 1, "msg": "实例不存在", "data": []}
        return HttpResponse(json.dumps(result), content_type="application/json")
    db_name = request.POST.get("db_name")
    schema_name = request.POST.get("schema_name")
    tb_name = request.POST.get("tb_name")

    result = {"status": 0, "msg": "ok", "data": []}

    try:
        query_engine = get_engine(instance=instance)
        db_name = query_engine.escape_string(db_name)
        schema_name = query_engine.escape_string(schema_name)
        tb_name = query_engine.escape_string(tb_name)
        query_result = query_engine.describe_table(
            db_name, tb_name, schema_name=schema_name
        )
        result["data"] = query_result.__dict__
    except Exception as msg:
        result["status"] = 1
        result["msg"] = str(msg)
    if result["data"].get("error"):
        result["status"] = 1
        result["msg"] = result["data"]["error"]
    return HttpResponse(json.dumps(result), content_type="application/json")

HEALTH_CACHE_TTL = 3600
HEALTH_CACHE_PREFIX = "insHealth:"


def _probe_instance(inst):
    close_old_connections()
    spec = _parse_spec(getattr(inst, "service_name", "") or "")
    cpu = spec["cpu"] or 2
    mem_mb = spec["mem"] or 4096
    conn_max = max(50, int(mem_mb / 8))
    qps_max = max(50, int(cpu) * 800)
    data = {
        "id": inst.id,
        "health": "down",
        "latency_ms": "-",
        "conn": 0,
        "conn_max": conn_max,
        "conn_pct": 0,
        "qps": 0,
        "qps_max": qps_max,
        "qps_pct": 0,
        "cpu": cpu,
        "mem": mem_mb,
        "msg": "",
        "cached": False,
    }
    t0 = time.time()
    try:
        engine = get_engine(instance=inst)
        if inst.db_type == "mysql":
            r = engine.query(
                sql="SHOW GLOBAL STATUS WHERE Variable_name IN ('Threads_connected', 'Questions', 'Uptime');"
            )
            kv = {row[0]: row[1] for row in (r.rows or [])}
            threads = int(kv.get("Threads_connected") or 0)
            questions = int(kv.get("Questions") or 0)
            uptime = int(kv.get("Uptime") or 1)
            qps = round(questions / max(uptime, 1), 1)
            data.update({"health": "up", "conn": threads, "qps": qps})
        elif inst.db_type == "pgsql":
            r = engine.query(
                sql="SELECT (SELECT count(*) FROM pg_stat_activity) AS conn, coalesce((SELECT sum(xact_commit+xact_rollback) FROM pg_stat_database),0) AS tx, extract(epoch from now()-pg_postmaster_start_time()) AS up;"
            )
            conn, tx, up = (r.rows[0] if r.rows else (0, 0, 1))
            qps = round(float(tx or 0) / max(float(up or 1), 1.0), 1)
            data.update({"health": "up", "conn": int(conn or 0), "qps": qps})
        else:
            engine.query(sql="SELECT 1")
            data.update({"health": "up"})
        try:
            engine.close()
        except Exception:
            pass
        latency_ms = int((time.time() - t0) * 1000)
        data.update(
            {
                "latency_ms": latency_ms,
                "conn_pct": round(float(data["conn"]) * 100.0 / conn_max, 1),
                "qps_pct": round(float(data["qps"] or 0) * 100.0 / qps_max, 1),
            }
        )
    except Exception as e:
        data["msg"] = str(e)[:180]
        data["latency_ms"] = int((time.time() - t0) * 1000)
    finally:
        close_old_connections()
    return data


def _cache_get(instance_id):
    try:
        r = get_redis_connection("default")
        raw = r.get(f"{HEALTH_CACHE_PREFIX}{instance_id}")
        if raw:
            data = json.loads(raw)
            data["cached"] = True
            return data
    except Exception:
        return None
    return None


def _cache_set(instance_id, data):
    try:
        r = get_redis_connection("default")
        payload = dict(data)
        payload["cached"] = False
        r.setex(f"{HEALTH_CACHE_PREFIX}{instance_id}", HEALTH_CACHE_TTL, json.dumps(payload))
    except Exception:
        pass


@permission_required("sql.menu_instance_list", raise_exception=True)
def health(request):
    """巡检拨测 + 连接/QPS 容量水位，默认读 1 小时缓存"""
    instance_id = request.GET.get("instance_id") or request.POST.get("instance_id")
    refresh = str(request.GET.get("refresh") or request.POST.get("refresh") or "") in ("1", "true", "True")
    result = {"status": 1, "msg": "", "data": {}}
    try:
        inst = Instance.objects.get(id=instance_id)
    except Instance.DoesNotExist:
        result["msg"] = "实例不存在"
        return HttpResponse(json.dumps(result), content_type="application/json")
    if not refresh:
        cached = _cache_get(inst.id)
        if cached:
            return HttpResponse(json.dumps({"status": 0, "msg": "ok", "data": cached}, cls=ExtendJSONEncoder, bigint_as_string=True), content_type="application/json")
    data = _probe_instance(inst)
    _cache_set(inst.id, data)
    return HttpResponse(json.dumps({"status": 0, "msg": "ok", "data": data}, cls=ExtendJSONEncoder, bigint_as_string=True), content_type="application/json")


@permission_required("sql.menu_instance_list", raise_exception=True)
def health_batch(request):
    """并发采集当前页实例指标，优先返回缓存"""
    raw_ids = request.GET.get("ids") or request.POST.get("ids") or ""
    refresh = str(request.GET.get("refresh") or request.POST.get("refresh") or "") in ("1", "true", "True")
    try:
        ids = [int(x) for x in str(raw_ids).split(",") if str(x).strip().isdigit()]
    except Exception:
        ids = []
    ids = ids[:100]
    inst_map = {i.id: i for i in Instance.objects.filter(id__in=ids)}
    rows = []
    missing = []
    for iid in ids:
        inst = inst_map.get(iid)
        if not inst:
            continue
        cached = None if refresh else _cache_get(iid)
        if cached:
            rows.append(cached)
        else:
            missing.append(inst)
    if missing:
        with ThreadPoolExecutor(max_workers=min(4, len(missing))) as pool:
            futures = {pool.submit(_probe_instance, inst): inst for inst in missing}
            for fut, inst in futures.items():
                try:
                    data = fut.result(timeout=3)
                except Exception as e:
                    spec = _parse_spec(getattr(inst, "service_name", "") or "")
                    cpu = spec["cpu"] or 2
                    mem_mb = spec["mem"] or 4096
                    data = {
                        "id": inst.id,
                        "health": "down",
                        "latency_ms": 3000,
                        "conn": 0,
                        "conn_max": max(50, int(mem_mb / 8)),
                        "conn_pct": 0,
                        "qps": 0,
                        "qps_max": max(50, int(cpu) * 800),
                        "qps_pct": 0,
                        "cpu": cpu,
                        "mem": mem_mb,
                        "msg": str(e)[:180] or "probe timeout",
                        "cached": False,
                    }
                _cache_set(data["id"], data)
                rows.append(data)
    return HttpResponse(json.dumps({"status": 0, "msg": "ok", "rows": rows}, cls=ExtendJSONEncoder, bigint_as_string=True), content_type="application/json")


def _parse_spec(text):
    cpu = 0
    mem = 0
    cls = ""
    for part in (text or "").split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        if k == "cpu":
            try:
                cpu = int(float(v))
            except Exception:
                cpu = 0
        elif k == "mem":
            try:
                mem = int(float(v))
            except Exception:
                mem = 0
        elif k == "cls":
            cls = v
    return {"cpu": cpu, "mem": mem, "cls": cls}
