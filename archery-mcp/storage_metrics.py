"""Cloud RDS storage metrics collector.

Queries Alibaba Cloud and AWS RDS APIs for disk usage, then caches results
for CACHE_TTL seconds so the monitoring page doesn't hammer cloud APIs on
every refresh.
"""

import os
import re
import time
import traceback
from typing import Any, Optional

CACHE_TTL = int(os.environ.get("STORAGE_CACHE_TTL", "300"))  # 5 min

# Alibaba Cloud credentials (optional — metrics silently skipped when absent)
ALI_AK = os.environ.get("ALI_ACCESS_KEY_ID", "")
ALI_SK = os.environ.get("ALI_ACCESS_KEY_SECRET", "")
ALI_REGION = os.environ.get("ALI_REGION_ID", "cn-beijing")

# AWS credentials (optional)
AWS_AK = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SK = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")

# ── Alibaba Cloud helpers ───────────────────────────────────────

_ali_client = None


def _get_ali_client():
    global _ali_client
    if _ali_client is not None:
        return _ali_client
    if not ALI_AK or not ALI_SK:
        return None
    try:
        from alibabacloud_rds20140815.client import Client
        from alibabacloud_tea_openapi.models import Config

        config = Config(
            access_key_id=ALI_AK,
            access_key_secret=ALI_SK,
            endpoint="rds.aliyuncs.com",
            region_id=ALI_REGION,
        )
        _ali_client = Client(config)
        return _ali_client
    except Exception:
        traceback.print_exc()
        return None


def _ali_instance_id_from_host(host: str) -> Optional[str]:
    """Extract pgm-xxx or rm-xxx RDS instance ID from hostname."""
    m = re.match(r"((?:pgm|pgr|rm|rr)-[a-z0-9]+)", host)
    return m.group(1) if m else None


def _ali_fetch_storage(rds_id: str) -> dict:
    """Fetch storage metrics for one Alibaba Cloud RDS instance."""
    client = _get_ali_client()
    if client is None:
        return {}
    try:
        from alibabacloud_rds20140815 import models

        # Get total allocated storage
        attr_req = models.DescribeDBInstanceAttributeRequest(dbinstance_id=rds_id)
        attr_resp = client.describe_dbinstance_attribute(attr_req)
        items = attr_resp.body.items.dbinstance_attribute
        if not items:
            return {}
        attr = items[0]
        total_gb = attr.dbinstance_storage or 0
        cpu = attr.dbinstance_cpu
        mem_mb = attr.dbinstance_memory or 0
        max_conn = attr.max_connections
        max_iops = attr.max_iops
        engine = f"{attr.engine} {attr.engine_version}"
        category = attr.category or ""
        spec = attr.dbinstance_class or ""

        # Get actual disk usage
        usage_req = models.DescribeResourceUsageRequest(dbinstance_id=rds_id)
        usage_resp = client.describe_resource_usage(usage_req)
        body = usage_resp.body
        disk_used_bytes = int(body.disk_used or 0)
        data_size_bytes = int(body.data_size or 0)
        log_size_bytes = int(body.log_size or 0)

        disk_used_gb = round(disk_used_bytes / (1024**3), 2)
        data_size_gb = round(data_size_bytes / (1024**3), 2)
        log_size_gb = round(log_size_bytes / (1024**3), 2)
        disk_pct = round(disk_used_gb / total_gb * 100, 1) if total_gb else 0

        return {
            "cloud": "aliyun",
            "rds_id": rds_id,
            "disk_total_gb": total_gb,
            "disk_used_gb": disk_used_gb,
            "disk_pct": disk_pct,
            "data_size_gb": data_size_gb,
            "log_size_gb": log_size_gb,
            "cpu": cpu,
            "mem_mb": mem_mb,
            "max_conn": max_conn,
            "max_iops": max_iops,
            "engine": engine,
            "category": category,
            "spec": spec,
        }
    except Exception as e:
        traceback.print_exc()
        return {"cloud": "aliyun", "rds_id": rds_id, "error": str(e)}


# ── AWS helpers ─────────────────────────────────────────────────

_aws_rds_client = None


def _get_aws_rds_client():
    global _aws_rds_client
    if _aws_rds_client is not None:
        return _aws_rds_client
    if not AWS_AK or not AWS_SK:
        return None
    try:
        import boto3

        _aws_rds_client = boto3.client(
            "rds",
            aws_access_key_id=AWS_AK,
            aws_secret_access_key=AWS_SK,
            region_name=AWS_REGION,
        )
        return _aws_rds_client
    except Exception:
        traceback.print_exc()
        return None


def _aws_instance_id_from_host(host: str) -> Optional[str]:
    """Extract RDS instance identifier from AWS hostname."""
    # e.g. tripo-internal.c1eakwiuo7nt.us-west-2.rds.amazonaws.com
    if "rds.amazonaws.com" not in host:
        return None
    parts = host.split(".")
    return parts[0] if parts else None


def _aws_fetch_storage(rds_id: str) -> dict:
    """Fetch storage metrics for one AWS RDS instance."""
    client = _get_aws_rds_client()
    if client is None:
        return {}
    try:
        resp = client.describe_db_instances(DBInstanceIdentifier=rds_id)
        instances = resp.get("DBInstances", [])
        if not instances:
            return {}
        inst = instances[0]
        total_gb = inst.get("AllocatedStorage", 0)
        cpu = inst.get("ProcessorFeatures", [])
        spec = inst.get("DBInstanceClass", "")
        engine = f"{inst.get('Engine', '')} {inst.get('EngineVersion', '')}"

        # AWS doesn't have a direct disk-usage API like Aliyun;
        # we'd need CloudWatch FreeStorageSpace metric. For now,
        # return what we have and mark disk_used as unavailable.
        return {
            "cloud": "aws",
            "rds_id": rds_id,
            "disk_total_gb": total_gb,
            "disk_used_gb": None,
            "disk_pct": None,
            "engine": engine,
            "spec": spec,
        }
    except Exception as e:
        traceback.print_exc()
        return {"cloud": "aws", "rds_id": rds_id, "error": str(e)}


# ── Collector ───────────────────────────────────────────────────


class StorageMetricsCollector:
    """Collects and caches storage metrics for Archery instances."""

    def __init__(self):
        self._cache: dict[int, dict] = {}
        self._cache_time: float = 0

    async def collect(self, instances: list[dict]) -> dict[str, Any]:
        """Return {instance_id: metrics_dict} for all instances.

        Uses a TTL-based cache so cloud API calls are rate-limited.
        """
        now = time.time()
        if self._cache and (now - self._cache_time) < CACHE_TTL:
            return self._cache

        result: dict[int, dict] = {}
        for inst in instances:
            iid = inst.get("id")
            host = inst.get("host", "")
            cloud = inst.get("cloud", "")

            if not host:
                continue

            metrics: dict = {}
            if "aliyuncs.com" in host or cloud == "aliyun":
                rds_id = _ali_instance_id_from_host(host)
                if rds_id:
                    metrics = _ali_fetch_storage(rds_id)
            elif "amazonaws.com" in host or cloud == "aws":
                rds_id = _aws_instance_id_from_host(host)
                if rds_id:
                    metrics = _aws_fetch_storage(rds_id)

            if metrics:
                result[iid] = metrics

        self._cache = result
        self._cache_time = now
        return result
