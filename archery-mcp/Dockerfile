FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --progress-bar off --no-build-isolation \
    "mcp[cli]" httpx \
    alibabacloud-rds20140815 alibabacloud-tea-openapi 2>/dev/null || \
    pip install --no-cache-dir "mcp[cli]" httpx alibabacloud-rds20140815 alibabacloud-tea-openapi

COPY archery_client.py server.py storage_metrics.py ./

ENV ARCHERY_URL=http://localhost:9123
ENV ARCHERY_USERNAME=admin
ENV ARCHERY_PASSWORD=Admin@2026!
ENV MCP_PORT=8080
ENV MCP_TRANSPORT=streamable-http

# Cloud API credentials (set via K8s env/secrets)
ENV ALI_ACCESS_KEY_ID=""
ENV ALI_ACCESS_KEY_SECRET=""
ENV ALI_REGION_ID="cn-beijing"

EXPOSE 8080

CMD ["python", "server.py"]
