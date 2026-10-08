#!/bin/sh
set -e
# Patch Archery source files for instancemonitor page
cp -a /opt/archery/sql/views.py /opt/archery-patch/views.py
cp -a /opt/archery/sql/urls.py  /opt/archery-patch/urls.py

# Add instancemonitor view
if ! grep -q 'def instancemonitor' /opt/archery-patch/views.py; then
  cat >> /opt/archery-patch/views.py << 'VIEWEOF'


def instancemonitor(request):
    from sql.models import InstanceTag
    from sql.engines import engine_map
    tags = InstanceTag.objects.filter(active=True)
    return render(request, "instancemonitor.html", {"tags": tags, "engines": engine_map})
VIEWEOF
  echo "patched views.py"
fi

# Add instancemonitor route
if ! grep -q 'instancemonitor' /opt/archery-patch/urls.py; then
  sed -i 's/^]$/    path("instancemonitor\/", views.instancemonitor),\n]/' /opt/archery-patch/urls.py
  echo "patched urls.py"
fi
