#!/bin/sh
set -eu
DB="${SCHEMASHIFT_MONITOR_DB:-/data/monitor.sqlite3}"
SEED="${MONITOR_SEED_DB:-/opt/seed/monitor.sqlite3}"
mkdir -p "$(dirname "$DB")"
if [ ! -f "$DB" ] && [ -f "$SEED" ]; then
  cp "$SEED" "$DB"
  echo "Seeded monitor DB from $SEED"
fi
export SCHEMASHIFT_MONITOR_PROXY="${SCHEMASHIFT_MONITOR_PROXY:-1}"
export SCHEMASHIFT_MONITOR_ORIGIN="${SCHEMASHIFT_MONITOR_ORIGIN:-http://localhost:5173}"
python -m monitoring.api --db "$DB" --port 8766 --bind 127.0.0.1 &
# Wait briefly for loopback API
i=0
while [ "$i" -lt 30 ]; do
  if wget -q -O /dev/null http://127.0.0.1:8766/api/monitor/snapshot 2>/dev/null; then
    break
  fi
  i=$((i + 1))
  sleep 0.2
done
exec nginx -g 'daemon off;'
