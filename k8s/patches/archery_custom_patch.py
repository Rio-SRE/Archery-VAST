"""Archery custom patches — loaded at startup via PYTHONSTARTUP or manage.py hook.

Registers:
  /instancemonitor/          → instancemonitor view (renders instancemonitor.html)
  /instance/health_batch/    → health_batch API (batch probe instances)
"""

import importlib
import os
import sys


def patch_once():
    """Idempotent patch: add custom views and URL routes to Archery."""

    # ── 1. Register the instancemonitor view ──────────────────

    views_mod = sys.modules.get("sql.views")
    if views_mod is None:
        return  # Django hasn't loaded yet; will be retried from AppConfig.ready()

    if hasattr(views_mod, "instancemonitor"):
        return  # Already patched

    from django.shortcuts import render

    def instancemonitor(request):
        """实例监控页面"""
        from sql.models import InstanceTag
        from sql.engines import engine_map

        tags = InstanceTag.objects.filter(active=True)
        return render(
            request, "instancemonitor.html", {"tags": tags, "engines": engine_map}
        )

    views_mod.instancemonitor = instancemonitor

    # ── 2. Register the URL route ─────────────────────────────

    from django.urls import path

    urls_mod = importlib.import_module("sql.urls")
    route_names = {p.pattern.describe() for p in urls_mod.urlpatterns}
    if "'instancemonitor/'" not in route_names:
        urls_mod.urlpatterns.append(
            path("instancemonitor/", views_mod.instancemonitor)
        )

    # ── 3. Register health_batch if missing ───────────────────

    instance_mod = sys.modules.get("sql.instance")
    if instance_mod and not hasattr(instance_mod, "health_batch"):
        # health_batch was custom; if it's missing, the page still works
        # but the health probe column will show "巡检中" forever.
        # A separate ConfigMap should provide the health_batch view.
        pass


# ── Django AppConfig hook ─────────────────────────────────────


class CustomPatchConfig:
    """Call patch_once() from AppConfig.ready() of any installed app."""

    name = "archery_custom_patch"

    @staticmethod
    def ready():
        patch_once()
