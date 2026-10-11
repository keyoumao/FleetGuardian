#!/usr/bin/env bash
set -euo pipefail

API=https://console-api.akash.network
ROOT="$(cd "$(dirname "$0")" && pwd)"
SDL="$ROOT/deploy.yaml"
ENV_FILE="${ENV_FILE:-/Users/keyoumao/Documents/SchemaShiftAuditor/.env}"

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
: "${AKASH_API_KEY:?AKASH_API_KEY missing}"

echo "=== Create deployment ==="
RESPONSE=$(curl -sS -X POST "$API/v1/deployments" \
  -H "x-api-key: $AKASH_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -nc --rawfile sdl "$SDL" '{data: {sdl: $sdl, name: "fleetguardian-demo"}}')")
echo "$RESPONSE" | jq '{dseq: .data.dseq, name: .data.name, code: .code, message: .message, error: .error}'
DSEQ=$(echo "$RESPONSE" | jq -r '.data.dseq // empty')
if [[ -z "$DSEQ" ]]; then
  echo "$RESPONSE" | jq .
  exit 1
fi
echo "DSEQ=$DSEQ" | tee "$ROOT/dseq.txt"

echo "=== Wait for bids ==="
BIDS=""
COUNT=0
for i in $(seq 1 24); do
  BIDS=$(curl -sS "$API/v1/bids?dseq=$DSEQ" -H "x-api-key: $AKASH_API_KEY")
  COUNT=$(echo "$BIDS" | jq '[.data[]? | select(.bid.state == "open")] | length')
  echo "attempt $i: open bids=$COUNT"
  [[ "$COUNT" -gt 0 ]] && break
  sleep 5
done
if [[ "$COUNT" -eq 0 ]]; then
  echo "$BIDS" | jq .
  exit 2
fi
echo "$BIDS" | jq '[.data[]? | select(.bid.state=="open") | {provider: .bid.id.provider, price: .bid.price.amount}] | sort_by(.price|tonumber) | .[0:6]'

echo "=== Accept bid ==="
LEASE_OK=""
N=$(echo "$BIDS" | jq '[.data[] | select(.bid.state == "open")] | length')
for idx in $(seq 0 $((N - 1))); do
  BID=$(echo "$BIDS" | jq -c --argjson i "$idx" '[.data[] | select(.bid.state == "open")] | sort_by(.bid.price.amount | tonumber) | .[$i].bid.id')
  echo "Trying bid $idx: $BID"
  LEASE_RESP=$(curl -sS -X POST "$API/v1/leases" \
    -H "x-api-key: $AKASH_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -nc --argjson id "$BID" '{leases: [{dseq: $id.dseq, gseq: $id.gseq, oseq: $id.oseq, provider: $id.provider}]}')")
  echo "$LEASE_RESP" | jq '{lease: .data.leases[0].id, code: .code, message: .message, error: .error}'
  OK=$(echo "$LEASE_RESP" | jq -r '.data.leases[0].id.dseq // empty')
  if [[ -n "$OK" ]]; then
    LEASE_OK=1
    break
  fi
done
[[ -n "$LEASE_OK" ]] || exit 3

echo "=== Wait until available ==="
for i in $(seq 1 48); do
  curl -sS "$API/v1/deployments/$DSEQ" -H "x-api-key: $AKASH_API_KEY" -o /tmp/fg-dep.json
  python3 - <<'PY'
import json
from pathlib import Path
raw = Path('/tmp/fg-dep.json').read_bytes()
clean = bytes(b if b >= 32 or b in (9, 10, 13) else 32 for b in raw)
data = json.loads(clean)
leases = (data.get('data') or {}).get('leases') or []
status = (leases[0].get('status') if leases else None) or {}
svc = (status.get('services') or {}).get('web') or {}
avail = svc.get('available') or 0
uris = svc.get('uris') or []
host = uris[0] if uris else ''
print(f'available={avail} host={host or "none"}')
root = Path('/Users/keyoumao/Documents/FleetGuardian/deploy')
if avail >= 1 and host:
    (root / 'url.txt').write_text(f'http://{host}\n')
PY
  [[ -f "$ROOT/url.txt" ]] && break
  sleep 5
done

if [[ ! -f "$ROOT/url.txt" ]]; then
  echo "Timed out waiting for service"
  python3 -c 'from pathlib import Path; print(Path("/tmp/fg-dep.json").read_text()[:3000])'
  exit 4
fi

URL=$(cat "$ROOT/url.txt")
echo "URL=$URL"
echo "=== Smoke checks ==="
curl -sS -I --max-time 30 "$URL" | head -15
curl -sS --max-time 30 "$URL/schema-audit.json" -o /tmp/fg-schema.json
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('/tmp/fg-schema.json').read_text())
print({k: d.get(k) for k in ('source', 'complete', 'model', 'provider', 'status')})
PY
curl -sS --max-time 30 -H "Origin: $URL" "$URL/api/monitor/snapshot" -o /tmp/fg-snap.json
python3 - <<'PY'
import json
from pathlib import Path
d = json.loads(Path('/tmp/fg-snap.json').read_text())
print('monitor totalEvents', d.get('totalEvents'), 'incidents', len(d.get('incidents', [])), d.get('incidentCounts'))
PY
curl -sS --max-time 30 "$URL/" -o /tmp/fg-index.html
python3 - <<'PY'
import re
from pathlib import Path
html = Path('/tmp/fg-index.html').read_text()
print(html[:160].replace('\n', ' '))
m = re.search(r'/assets/[^"\s]+\.js', html)
Path('/tmp/fg-js-path.txt').write_text(m.group(0) if m else '')
print('js', m.group(0) if m else 'missing')
PY
JS=$(cat /tmp/fg-js-path.txt)
if [[ -n "$JS" ]]; then
  if curl -sS --max-time 30 "$URL$JS" | grep -q "Revision demo"; then
    echo "revision_demo_string=present"
  else
    echo "revision_demo_string=MISSING"
  fi
fi
echo "DONE dseq=$DSEQ url=$URL"
