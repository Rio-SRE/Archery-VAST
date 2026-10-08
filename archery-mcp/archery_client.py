"""Archery REST API Client — async, session-based authentication (web API)."""

import httpx
import re
from typing import Any


class ArcheryClient:
    """Wrapper around Archery's web API using session/cookie auth (async)."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self._session: httpx.AsyncClient | None = None
        self._csrf: str = ""

    async def _ensure_session(self) -> None:
        if self._session is not None:
            return
        await self._login()

    async def _login(self) -> None:
        if self._session is not None:
            await self._session.aclose()
        self._session = httpx.AsyncClient(timeout=30.0, follow_redirects=False)
        resp = await self._session.get(f"{self.base_url}/login/", follow_redirects=True)
        for line in resp.text.split("\n"):
            if "csrfmiddlewaretoken" in line and 'value="' in line:
                self._csrf = line.split('value="')[1].split('"')[0]
                break
        await self._session.post(
            f"{self.base_url}/authenticate/",
            data={
                "csrfmiddlewaretoken": self._csrf,
                "username": self.username,
                "password": self.password,
            },
            headers={"Referer": f"{self.base_url}/login/"},
            follow_redirects=True,
        )
        self._csrf = self._session.cookies.get("csrftoken", "")

    async def _ajax_get(self, path: str, params: dict | None = None) -> Any:
        await self._ensure_session()
        resp = await self._session.get(
            f"{self.base_url}/{path.lstrip('/')}",
            params=params,
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
        if resp.status_code == 302 or "/login" in str(resp.headers.get("location", "")):
            await self._login()
            resp = await self._session.get(
                f"{self.base_url}/{path.lstrip('/')}",
                params=params,
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
        resp.raise_for_status()
        return resp.json()

    async def _ajax_post(self, path: str, data: dict | None = None) -> Any:
        await self._ensure_session()
        resp = await self._session.post(
            f"{self.base_url}/{path.lstrip('/')}",
            data=data,
            headers={
                "X-CSRFToken": self._csrf,
                "X-Requested-With": "XMLHttpRequest",
                "Referer": f"{self.base_url}/sqlquery/",
            },
        )
        if resp.status_code == 302 or "/login" in str(resp.headers.get("location", "")):
            await self._login()
            resp = await self._session.post(
                f"{self.base_url}/{path.lstrip('/')}",
                data=data,
                headers={
                    "X-CSRFToken": self._csrf,
                    "X-Requested-With": "XMLHttpRequest",
                    "Referer": f"{self.base_url}/sqlquery/",
                },
            )
        resp.raise_for_status()
        return resp.json()

    # ── Instance metadata cache ────────────────────────────────────

    _instance_cache: list[dict] = []

    async def _refresh_instance_cache(self) -> None:
        try:
            data = await self._ajax_post(
                "instance/list/",
                {"limit": 500, "offset": 0, "sortName": "id", "sortOrder": "asc", "scope": "all"},
            )
            self._instance_cache = data.get("rows", data.get("data", []))
        except Exception:
            pass

    async def _get_instance_type(self, instance_name: str) -> str:
        if not self._instance_cache:
            await self._refresh_instance_cache()
        for inst in self._instance_cache:
            if inst.get("instance_name") == instance_name:
                return inst.get("type", "")
        return ""

    def _is_test_instance(self, instance_name: str) -> bool:
        return "test" in (instance_name or "").lower()

    def _is_master(self, instance_name: str, inst_type: str) -> bool:
        return inst_type != "slave"

    async def assert_slave(self, instance_name: str) -> None:
        inst_type = await self._get_instance_type(instance_name)
        if self._is_test_instance(instance_name):
            return
        if self._is_master(instance_name, inst_type):
            raise PermissionError(
                f"MCP 安全限制：禁止查询主库 '{instance_name}' (type={inst_type})，请使用对应的从库。"
            )

    # ── Instance Management ──────────────────────────────────────

    async def list_instances(self, scope: str = "all") -> list[dict]:
        try:
            data = await self._ajax_post(
                "instance/list/",
                {
                    "limit": 200,
                    "offset": 0,
                    "sortName": "id",
                    "sortOrder": "asc",
                    "scope": scope,
                },
            )
            return data.get("rows", data.get("data", []))
        except Exception:
            try:
                data = await self._ajax_get("group/user_all_instances/")
                return data.get("data", [])
            except Exception:
                return []

    async def list_instances_admin(self) -> list[dict]:
        """List instances with host/port info (admin view)."""
        data = await self._ajax_post(
            "instance/list/",
            {"limit": 200, "offset": 0, "sortName": "id", "sortOrder": "asc"},
        )
        return data.get("rows", [])

    async def get_instance_health(self, instance_id: int) -> dict:
        data = await self._ajax_get("instance/health/", {"instance_id": instance_id})
        if isinstance(data, dict) and "data" in data:
            return data.get("data") or {}
        return data if isinstance(data, dict) else {}

    async def get_instance_resource(
        self, instance_name: str, resource_type: str,
        db_name: str = "", schema_name: str = "", tb_name: str = ""
    ) -> list:
        params = {
            "instance_name": instance_name,
            "resource_type": resource_type,
        }
        if db_name:
            params["db_name"] = db_name
        if schema_name:
            params["schema_name"] = schema_name
        if tb_name:
            params["tb_name"] = tb_name
        data = await self._ajax_get("instance/instance_resource/", params)
        return data.get("data", [])

    async def list_databases(self, instance_name: str) -> list[str]:
        return await self.get_instance_resource(instance_name, "database")

    async def list_tables(self, instance_name: str, db_name: str, schema_name: str = "") -> list[str]:
        return await self.get_instance_resource(instance_name, "table", db_name, schema_name)

    async def describe_table(
        self, instance_name: str, db_name: str, tb_name: str, schema_name: str = ""
    ) -> list[str]:
        return await self.get_instance_resource(instance_name, "column", db_name, schema_name, tb_name)

    # ── SQL Query ────────────────────────────────────────────────

    async def execute_query(
        self, instance_name: str, db_name: str, sql: str,
        schema_name: str = "", limit: int = 100,
    ) -> dict:
        return await self._ajax_post("query/", {
            "instance_name": instance_name,
            "db_name": db_name,
            "schema_name": schema_name,
            "tb_name": "",
            "sql_content": sql,
            "limit_num": limit,
        })

    # ── SQL Workflow ─────────────────────────────────────────────

    async def submit_workflow(
        self, workflow_name: str, instance_name: str, db_name: str,
        sql_content: str, group_id: int = 1, is_backup: bool = False,
    ) -> dict:
        return await self._ajax_post("autoreview/", {
            "workflow_name": workflow_name,
            "group_id": group_id,
            "instance_name": instance_name,
            "db_name": db_name,
            "is_backup": "True" if is_backup else "False",
            "engineer": self.username,
            "sql_content": sql_content,
        })

    async def list_workflows(self, limit: int = 50) -> list[dict]:
        await self._ensure_session()
        page = await self._session.get(f"{self.base_url}/sqlworkflow/")
        workflows = []
        for m in re.finditer(r'href="/detail/(\d+)/"', page.text):
            wf_id = int(m.group(1))
            workflows.append({"id": wf_id})
        return workflows[:limit]

    async def get_workflow_detail(self, workflow_id: int) -> dict:
        await self._ensure_session()
        resp = await self._session.get(f"{self.base_url}/detail/{workflow_id}/")
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}"}
        html = resp.text
        info = {"id": workflow_id}
        for status in ["workflow_finish", "workflow_review_pass", "workflow_manreviewing", "workflow_abort"]:
            if status in html:
                info["status"] = status
                break
        m = re.search(r'<th>工单名称</th>\s*<td[^>]*>([^<]+)', html)
        if m:
            info["workflow_name"] = m.group(1).strip()
        return info

    async def approve_workflow(self, workflow_id: int, remark: str = "approved") -> str:
        await self._ensure_session()
        resp = await self._session.post(
            f"{self.base_url}/passed/",
            data={
                "csrfmiddlewaretoken": self._csrf,
                "workflow_id": workflow_id,
                "audit_remark": remark,
            },
            headers={"Referer": f"{self.base_url}/detail/{workflow_id}/"},
        )
        return "ok" if resp.status_code in (200, 302) else f"error: {resp.status_code}"

    async def reject_workflow(self, workflow_id: int, remark: str = "rejected") -> str:
        await self._ensure_session()
        resp = await self._session.post(
            f"{self.base_url}/cancel/",
            data={
                "csrfmiddlewaretoken": self._csrf,
                "workflow_id": workflow_id,
                "audit_remark": remark,
            },
            headers={"Referer": f"{self.base_url}/detail/{workflow_id}/"},
        )
        return "ok" if resp.status_code in (200, 302) else f"error: {resp.status_code}"

    async def execute_workflow(self, workflow_id: int) -> str:
        await self._ensure_session()
        resp = await self._session.post(
            f"{self.base_url}/execute/",
            data={
                "csrfmiddlewaretoken": self._csrf,
                "workflow_id": workflow_id,
            },
            headers={
                "X-CSRFToken": self._csrf,
                "Referer": f"{self.base_url}/detail/{workflow_id}/",
            },
        )
        return "ok" if resp.status_code in (200, 302) else f"error: {resp.status_code}"

    # ── Instance Account ─────────────────────────────────────────

    async def list_instance_accounts(self, instance_id: int) -> list[dict]:
        data = await self._ajax_post("instance/user/list", {"instance_id": instance_id})
        return data.get("data", data.get("rows", []))

    async def list_instance_databases(self, instance_id: int) -> list[dict]:
        data = await self._ajax_post("instance/database/list/", {"instance_id": instance_id})
        return data.get("data", data.get("rows", []))
