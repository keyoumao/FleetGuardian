"""Instrumentation for the live evaluation worker; monitoring is opt-in."""
import os
import sys
from monitoring.store import Store


def emit(run_id, kind, config_hash='', variant='', attempted=False, committed=False, blocked=False):
    path = os.environ.get('SCHEMASHIFT_MONITOR_DB')
    if not path: return
    try:
        Store(path).append({'event_id': run_id + '-' + kind, 'run_id': run_id,
            'agent': 'records-assistant', 'origin': 'live', 'execution': 'simulated',
            'kind': kind, 'config_hash': config_hash, 'variant': variant,
            'attempted': attempted, 'committed': committed, 'blocked': blocked})
    except Exception:
        print('MONITORING ERROR: event persistence failed; evaluation continues without a complete monitoring record.', file=sys.stderr)
