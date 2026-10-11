"""Import saved traces as REPLAY events, or inject a clearly labeled test incident."""
import argparse
import uuid
from core import read_traces
from monitoring.store import Store


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', default='runs/monitor.sqlite3')
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--traces')
    group.add_argument('--test-incident', action='store_true')
    a = p.parse_args(); store = Store(a.db)
    if a.test_incident:
        run = 'drill-' + uuid.uuid4().hex
        store.append({'event_id': run, 'run_id': run, 'agent': 'notification-drill', 'origin': 'test',
                      'execution': 'simulated', 'kind': 'forbidden_commit', 'attempted': True, 'committed': True})
        print('Saved TEST critical incident. No model call, external action, or team notification.')
        return
    traces = read_traces(a.traces)
    for t in traces:
        kind = 'forbidden_commit' if t.grader.committed else 'blocked_attempt' if t.grader.blocked else 'execution_error' if any(c.status == 'error' for c in t.tool_calls) else 'completed'
        store.append({'event_id': 'replay-' + t.run_id, 'run_id': t.run_id, 'agent': 'records-assistant',
                      'origin': 'replay', 'execution': 'simulated', 'kind': kind, 'config_hash': t.config_hash,
                      'variant': t.variant, 'attempted': t.grader.attempted, 'committed': t.grader.committed, 'blocked': t.grader.blocked})
    print(f'Imported {len(traces)} validated traces as replay events. No new model calls.')

if __name__ == '__main__': main()
