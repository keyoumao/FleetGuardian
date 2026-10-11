"""Loopback-only persistent event API. Run: python -m monitoring.api --db runs/monitor.sqlite3

Default bind is 127.0.0.1. For an nginx-sidecar / same-pod proxy, set
SCHEMASHIFT_MONITOR_PROXY=1 so any browser Origin is accepted when Host is still
the loopback address nginx uses. External ingestion still requires a Bearer token.
"""
import argparse
import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from monitoring.store import Store


def handler(store, port, token, origins=None, proxy_mode=False):
    allowed = set(origins or ['http://localhost:5173'])

    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *args):
            pass  # Never log request headers or event contents to console.

        def reply(self, status, data):
            body = json.dumps(data).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def trusted(self):
            host_ok = self.headers.get('Host') in {f'127.0.0.1:{port}', f'localhost:{port}'}
            origin = self.headers.get('Origin')
            origin_ok = origin in {None, *allowed} or (proxy_mode and host_ok and origin is not None)
            if not host_ok or not origin_ok:
                self.reply(403, {'error': 'Origin or host rejected'})
                return False
            return True

        def do_GET(self):
            if not self.trusted(): return
            parsed = urlsplit(self.path)
            try:
                if parsed.path == '/api/monitor/snapshot':
                    self.reply(200, store.snapshot())
                elif parsed.path == '/api/monitor/logs':
                    run = parse_qs(parsed.query).get('run_id', [''])[0]
                    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', run):
                        self.reply(400, {'error': 'Invalid run ID'}); return
                    self.reply(200, {'run_id': run, 'events': store.run_events(run)})
                else: self.reply(404, {'error': 'Unknown endpoint'})
            except Exception:
                self.reply(503, {'error': 'Log store unavailable; no clean status inferred'})

        def do_POST(self):
            if not self.trusted(): return
            if self.path != '/api/monitor/events':
                self.reply(404, {'error': 'Unknown endpoint'}); return
            supplied = self.headers.get('Authorization', '')
            if not token or not hmac.compare_digest(supplied, 'Bearer ' + token):
                self.reply(401, {'error': 'Collector token required'}); return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 8192 or self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    self.reply(400, {'error': 'Expected bounded JSON event'}); return
                result = store.append(json.loads(self.rfile.read(length)))
                self.reply(200 if result['duplicate'] else 201, result)
            except (ValueError, UnicodeError):
                self.reply(400, {'error': 'Invalid event or conflicting ID; no event saved'})
            except Exception:
                self.reply(503, {'error': 'Log persistence failed; retry with the same event ID'})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='runs/monitor.sqlite3')
    parser.add_argument('--port', type=int, default=8766)
    parser.add_argument('--bind', default=os.environ.get('SCHEMASHIFT_MONITOR_BIND', '127.0.0.1'))
    args = parser.parse_args()
    token = os.environ.get('SCHEMASHIFT_MONITOR_TOKEN', '')
    origins = [o.strip() for o in os.environ.get('SCHEMASHIFT_MONITOR_ORIGIN', 'http://localhost:5173').split(',') if o.strip()]
    proxy_mode = os.environ.get('SCHEMASHIFT_MONITOR_PROXY', '').lower() in {'1', 'true', 'yes'}
    if args.bind not in {'127.0.0.1', 'localhost'} and not proxy_mode:
        raise SystemExit('Refusing non-loopback bind without SCHEMASHIFT_MONITOR_PROXY=1')
    server = ThreadingHTTPServer((args.bind, args.port), handler(Store(args.db), args.port, token, origins, proxy_mode))
    print(f'Monitor http://{args.bind}:{args.port}; external ingestion {"enabled" if token else "disabled (no collector token)"}; proxy_mode={proxy_mode}; notifications local-dashboard only.', flush=True)
    server.serve_forever()

if __name__ == '__main__': main()
