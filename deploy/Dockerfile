# FleetGuardian static UI + SchemaShift live monitor (SQLite) behind nginx.
FROM python:3.12-slim-bookworm

RUN apt-get update \
  && apt-get install -y --no-install-recommends nginx wget \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY deploy/monitor-src/ /app/
RUN pip install --no-cache-dir 'pydantic>=2.7,<3'
COPY deploy/nginx.conf /etc/nginx/sites-available/fleetguardian
RUN rm -f /etc/nginx/sites-enabled/default /etc/nginx/conf.d/default.conf \
  && ln -sf /etc/nginx/sites-available/fleetguardian /etc/nginx/sites-enabled/fleetguardian \
  && nginx -t
COPY web/dist/ /usr/share/nginx/html/
RUN test -f /usr/share/nginx/html/index.html

COPY deploy/seed-monitor.sqlite3 /opt/seed/monitor.sqlite3
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh \
  && mkdir -p /data \
  && python -c "import monitoring.api, monitoring.store"

ENV SCHEMASHIFT_MONITOR_DB=/data/monitor.sqlite3 \
    SCHEMASHIFT_MONITOR_PROXY=1 \
    PYTHONUNBUFFERED=1

EXPOSE 80
VOLUME ["/data"]
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1/api/monitor/snapshot || exit 1

ENTRYPOINT ["/entrypoint.sh"]
