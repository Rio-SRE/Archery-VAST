"""Archery MCP Server — expose Archery SQL audit platform as MCP tools.

Supports both stdio (local) and streamable-http (remote) transports.
Includes a custom /api/storage endpoint for cloud RDS storage metrics.
"""

import json
import os
import time
import traceback
from mcp.server import MCPServer

from archery_client import ArcheryClient
from storage_metrics import StorageMetricsCollector

ARCHERY_URL = os.environ.get("ARCHERY_URL", "http://localhost:9123")
ARCHERY_USERNAME = os.environ.get("ARCHERY_USERNAME", "admin")
ARCHERY_PASSWORD = os.environ.get("ARCHERY_PASSWORD", "Admin@2026!")
MCP_PORT = int(os.environ.get("MCP_PORT", "8080"))
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "streamable-http")

mcp = MCPServer("archery")
client: ArcheryClient | None = None


def get_client() -> ArcheryClient:
    global client
    if client is None:
        client = ArcheryClient(ARCHERY_URL, ARCHERY_USERNAME, ARCHERY_PASSWORD)
    return client


def _fmt(data) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


# ── Instance Management ─────────────────────────────────────────


@mcp.tool()
async def list_instances(scope: str = "all") -> str:
    """List database instances registered in Archery.

    Args:
        scope: "manual" for operator-added instances, "imported" for scanned
            cloud instances, "all" for everything (default).
    """
    return _fmt(await get_client().list_instances(scope))


@mcp.tool()
async def list_databases(instance_name: str) -> str:
    """List all databases in a given instance (slave only).

    Args:
        instance_name: The name of the instance as registered in Archery.
    """
    await get_client().assert_slave(instance_name)
    return _fmt(await get_client().list_databases(instance_name))


@mcp.tool()
async def list_tables(instance_name: str, db_name: str, schema_name: str = "") -> str:
    """List all tables in a database (slave only).

    Args:
        instance_name: The instance name.
        db_name: The database name.
        schema_name: Schema name (required for PostgreSQL, e.g. "public").
    """
    await get_client().assert_slave(instance_name)
    return _fmt(await get_client().list_tables(instance_name, db_name, schema_name))


@mcp.tool()
async def describe_table(instance_name: str, db_name: str, tb_name: str, schema_name: str = "") -> str:
    """Describe table structure — list all columns (slave only).

    Args:
        instance_name: The instance name.
        db_name: The database name.
        tb_name: The table name.
        schema_name: Schema name (for PostgreSQL, e.g. "public").
    """
    await get_client().assert_slave(instance_name)
    return _fmt(await get_client().describe_table(instance_name, db_name, tb_name, schema_name))


# ── SQL Query ────────────────────────────────────────────────────


@mcp.tool()
async def execute_query(instance_name: str, db_name: str, sql: str, schema_name: str = "", limit: int = 100) -> str:
    """Execute a read-only SQL query on a database instance (slave only).

    Only SELECT/SHOW queries are allowed. DML/DDL must go through submit_workflow.
    Queries are restricted to slave/read-only instances for safety.

    Args:
        instance_name: The instance name.
        db_name: The database name.
        sql: The SQL query (SELECT, SHOW, etc.).
        schema_name: Schema name (for PostgreSQL).
        limit: Max rows to return (default 100).
    """
    await get_client().assert_slave(instance_name)
    data = await get_client().execute_query(instance_name, db_name, sql, schema_name, limit)
    status = data.get("status", -1)
    if status != 0:
        return f"Query error: {data.get('msg', 'unknown error')}"
    rows = data.get("data", {}).get("rows", [])
    cols = data.get("data", {}).get("column_list", [])
    return _fmt({"columns": cols, "rows": rows, "row_count": len(rows)})


# ── SQL Workflow (Change Management) ─────────────────────────────


@mcp.tool()
async def submit_workflow(workflow_name: str, instance_name: str, db_name: str, sql_content: str, group_id: int = 1) -> str:
    """Submit a SQL change workflow for review (DDL/DML).

    The workflow goes through: submit -> review -> execute.

    Args:
        workflow_name: A descriptive name (e.g. "add-phone-column").
        instance_name: The target instance name.
        db_name: The target database name.
        sql_content: The SQL statements to execute.
        group_id: Resource group ID (default 1).
    """
    return _fmt(await get_client().submit_workflow(workflow_name, instance_name, db_name, sql_content, group_id))


@mcp.tool()
async def list_workflows(limit: int = 20) -> str:
    """List recent SQL change workflows.

    Args:
        limit: Number of workflows to return (default 20).
    """
    return _fmt(await get_client().list_workflows(limit))


@mcp.tool()
async def get_workflow(workflow_id: int) -> str:
    """Get details of a specific SQL workflow.

    Args:
        workflow_id: The workflow ID.
    """
    return _fmt(await get_client().get_workflow_detail(workflow_id))


@mcp.tool()
async def review_workflow(workflow_id: int, action: str, remark: str = "") -> str:
    """Review (approve or reject) a pending SQL workflow.

    Args:
        workflow_id: The workflow ID to review.
        action: "pass" to approve, "reject" to reject.
        remark: Optional review comment.
    """
    c = get_client()
    if action == "pass":
        return await c.approve_workflow(workflow_id, remark or "approved")
    elif action == "reject":
        return await c.reject_workflow(workflow_id, remark or "rejected")
    return "Error: action must be 'pass' or 'reject'"


@mcp.tool()
async def execute_workflow(workflow_id: int) -> str:
    """Execute an approved SQL workflow.

    The workflow must be in "workflow_review_pass" status.

    Args:
        workflow_id: The workflow ID to execute.
    """
    return await get_client().execute_workflow(workflow_id)


# ── Instance Details ─────────────────────────────────────────────


@mcp.tool()
async def list_instance_accounts(instance_id: int) -> str:
    """List database accounts for an instance.

    Args:
        instance_id: The numeric ID of the instance.
    """
    return _fmt(await get_client().list_instance_accounts(instance_id))


@mcp.tool()
async def list_instance_databases(instance_id: int) -> str:
    """List databases managed by an instance (with metadata).

    Args:
        instance_id: The numeric ID of the instance.
    """
    return _fmt(await get_client().list_instance_databases(instance_id))


def _level(pct) -> str:
    try:
        p = float(pct)
    except (TypeError, ValueError):
        return "unknown"
    if p >= 80:
        return "critical"
    if p >= 60:
        return "warning"
    return "ok"


@mcp.tool()
async def get_instance_health(instance_id: int) -> str:
    """Probe one instance: health check, latency, connection watermark, QPS watermark.

    Args:
        instance_id: Numeric Archery instance ID.
    """
    data = await get_client().get_instance_health(instance_id)
    data["conn_level"] = _level(data.get("conn_pct"))
    data["qps_level"] = _level(data.get("qps_pct"))
    return _fmt(data)


@mcp.tool()
async def analyze_instance_capacity(
    scope: str = "all",
    warn_pct: float = 60,
    crit_pct: float = 80,
    limit: int = 50,
) -> str:
    """Analyze health-check / connection / QPS watermarks across instances.

    Args:
        scope: "manual", "imported", or "all".
        warn_pct: Warning threshold percent (default 60).
        crit_pct: Critical threshold percent (default 80).
        limit: Max instances to probe (default 50).
    """
    instances = await get_client().list_instances(scope)
    rows = []
    down = []
    hot = []
    for inst in instances[: max(1, int(limit))]:
        iid = inst.get("id")
        name = inst.get("instance_name") or inst.get("name") or str(iid)
        try:
            h = await get_client().get_instance_health(iid)
        except Exception as e:
            down.append({"id": iid, "name": name, "error": str(e)[:180]})
            continue
        conn_pct = float(h.get("conn_pct") or 0)
        qps_pct = float(h.get("qps_pct") or 0)
        item = {
            "id": iid,
            "name": name,
            "cloud": inst.get("cloud"),
            "type": inst.get("type"),
            "db_type": inst.get("db_type"),
            "health": h.get("health"),
            "latency_ms": h.get("latency_ms"),
            "conn": f"{h.get('conn')}/{h.get('conn_max')} ({conn_pct}%)",
            "qps": f"{h.get('qps')}/{h.get('qps_max')} ({qps_pct}%)",
            "conn_pct": conn_pct,
            "qps_pct": qps_pct,
            "conn_level": _level(conn_pct),
            "qps_level": _level(qps_pct),
        }
        rows.append(item)
        if h.get("health") != "up":
            down.append(item)
        elif conn_pct >= warn_pct or qps_pct >= warn_pct:
            hot.append(item)
    summary = {
        "probed": len(rows),
        "up": sum(1 for r in rows if r.get("health") == "up"),
        "down": len(down),
        "hot": len(hot),
        "hottest_conn": sorted(rows, key=lambda x: x.get("conn_pct") or 0, reverse=True)[:5],
        "hottest_qps": sorted(rows, key=lambda x: x.get("qps_pct") or 0, reverse=True)[:5],
        "down_or_error": down[:20],
        "warning_or_critical": hot[:20],
    }
    return _fmt(summary)


# ── Storage Metrics API (custom HTTP route) ─────────────────────

storage_collector = StorageMetricsCollector()


CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}


@mcp.custom_route("/api/storage", methods=["GET", "OPTIONS"])
async def storage_metrics_api(request):
    """Return storage metrics for all Archery instances."""
    from starlette.responses import JSONResponse, Response

    if request.method == "OPTIONS":
        return Response(status_code=204, headers=CORS_HEADERS)

    try:
        archery_client = get_client()
        instances = await archery_client.list_instances_admin()
        metrics = await storage_collector.collect(instances)
        return JSONResponse({"status": 0, "data": metrics}, headers=CORS_HEADERS)
    except Exception as e:
        traceback.print_exc()
        return JSONResponse({"status": 1, "msg": str(e), "data": {}}, headers=CORS_HEADERS)


# ── Entry Point ──────────────────────────────────────────────────


def main():
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
