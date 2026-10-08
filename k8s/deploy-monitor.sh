#!/bin/bash
# Deploy enhanced Archery instance monitoring template
# Usage: bash deploy-monitor.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NAMESPACE="archery"

echo "=== 1. Creating ConfigMap from template ==="
kubectl create configmap archery-monitor-template \
  --from-file=instancemonitor.html="$SCRIPT_DIR/templates/instancemonitor.html" \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

echo "=== 2. Applying Archery Deployment (with template volume mount) ==="
kubectl apply -f "$SCRIPT_DIR/archery.yaml"

echo "=== 3. Restarting Archery pod to pick up changes ==="
kubectl rollout restart deployment/archery -n "$NAMESPACE"
kubectl rollout status deployment/archery -n "$NAMESPACE" --timeout=120s

echo "=== Done. Refresh /instancemonitor/ to see new columns. ==="
