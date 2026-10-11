import { useEffect, useState } from "react";
import { Card, PageHeader } from "../components/ui";

type Event = { event_id: string; run_id: string; agent: string; origin: string; execution: string; kind: string; severity: string | null; received_at: string; config_hash: string; variant: string; attempted: boolean; committed: boolean; blocked: boolean };
type Snapshot = { totalEvents: number; serverTime: string; events: Event[]; incidents: Event[]; incidentCounts: Record<string, number> };
export default function LiveMonitor() {
  const [data, setData] = useState<Snapshot | null>(null);
  const [error, setError] = useState("");
  const [origin, setOrigin] = useState("all");
  useEffect(() => {
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const response = await fetch('/api/monitor/snapshot', {signal: controller.signal, cache: 'no-store'});
        if (!response.ok) throw new Error('Monitor unavailable. Start the local monitoring API on port 8766.');
        const value = await response.json() as Snapshot;
        if (!Array.isArray(value.events) || !Array.isArray(value.incidents)) throw new Error('Invalid monitor response.');
        if (!controller.signal.aborted) { setData(value); setError(""); }
      } catch (e) {
        if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Monitor disconnected.');
      } finally { if (!controller.signal.aborted) timer = setTimeout(poll, 2000); }
    }
    poll();
    return () => { controller.abort(); clearTimeout(timer); };
  }, []);
  const incidents = (data?.incidents || []).filter(e => origin === 'all' || e.origin === origin);
  const events = (data?.events || []).filter(e => origin === 'all' || e.origin === origin);
  const critical = incidents.filter(e => e.severity === 'critical');
  return <>
    <PageHeader title="Live security monitor" subtitle="Persistent agent events and incident evidence · local notifications only" />
    <div role="status" className={`mb-5 rounded-xl border p-4 text-sm ${error ? 'border-amber-700 text-amber-200' : 'border-sky-800 text-sky-200'}`}>
      {error || (data ? `Connected · refreshes every 2 seconds · last update ${new Date(data.serverTime).toLocaleTimeString()}` : 'Connecting to the local monitor…')}
      {error && data && <p className="mt-1">Showing saved results from the last successful fetch. Monitoring is not currently live.</p>}
    </div>
    <p className="mb-5 text-sm text-slate-400">Events are saved in the backend SQLite log store and survive page reloads. Live describes event collection; execution is labeled separately as real or simulated. Replay and test events are never new ASR trials. No Slack, email, Langfuse, or LangSmith notifications are sent.</p>
    <label className="mb-5 flex items-center gap-3 text-sm">Event provenance
      <select className="rounded-lg border border-slate-700 bg-slate-900 p-2" value={origin} onChange={e => setOrigin(e.target.value)}>
        <option value="all">All sources</option><option value="live">Live collection</option><option value="replay">Historical replay</option><option value="test">Test drills</option>
      </select>
    </label>
    {critical.length > 0 && <div role="alert" className="mb-5 rounded-xl border border-rose-600 bg-rose-950/40 p-4 text-rose-200">
      <strong>{critical.length} critical incident{critical.length === 1 ? '' : 's'} in the displayed records</strong>
      <p className="mt-1">{critical.filter(e => e.origin === 'test').length} test drills; {critical.filter(e => e.origin === 'replay').length} replay events; {critical.filter(e => e.origin === 'live').length} live events. Inspect execution labels before treating these as production incidents.</p>
    </div>}
    <div className="mb-5 grid gap-4 sm:grid-cols-3">
      <Card><p className="text-sm text-slate-400">Persisted events · all sources</p><p className="mt-2 text-3xl">{data?.totalEvents ?? '—'}</p></Card>
      <Card><p className="text-sm text-slate-400">Displayed incidents</p><p className="mt-2 text-3xl">{incidents.length}</p></Card>
      <Card><p className="text-sm text-slate-400">Notification destination</p><p className="mt-2 text-xl">Local dashboard</p></Card>
    </div>
    <Card><h2 className="mb-4 text-lg font-semibold">Incident inbox</h2>
      {!incidents.length && <p className="text-sm text-slate-400">No incidents in the selected saved records. This is not proof of safety or collector coverage.</p>}
      <div className="space-y-3">{incidents.map(event => <details key={event.event_id} className="rounded-lg border border-slate-700 p-3">
        <summary className="cursor-pointer text-sm"><span className={event.severity === 'critical' ? 'text-rose-300' : 'text-amber-300'}>{event.severity?.toUpperCase()}</span> · {event.kind} · {event.agent} <span className="ml-2 text-slate-400">{event.origin.toUpperCase()} / {event.execution}</span></summary>
        <p className="mt-3 break-all text-xs text-slate-400">Run: {event.run_id} · Received: {new Date(event.received_at).toLocaleString()}</p>
        <pre className="my-3 overflow-auto rounded bg-slate-950 p-3 text-xs">{JSON.stringify(event, null, 2)}</pre>
        <a className="text-sm text-sky-300 underline" href={`/api/monitor/logs?run_id=${encodeURIComponent(event.run_id)}`} target="_blank" rel="noreferrer">Open saved run logs (JSON)</a>
      </details>)}</div>
    </Card>
    <Card className="mt-5 overflow-x-auto"><h2 className="mb-4 text-lg font-semibold">Event stream · latest 100 saved events</h2>
      <table className="w-full whitespace-nowrap text-left text-xs"><thead><tr>{['Received', 'Agent', 'Event', 'Provenance', 'Execution'].map(h => <th className="p-2 text-slate-400" key={h}>{h}</th>)}</tr></thead>
        <tbody>{events.map(e => <tr key={e.event_id} className="border-t border-slate-800"><td className="p-2">{new Date(e.received_at).toLocaleTimeString()}</td><td className="p-2">{e.agent}</td><td className="p-2">{e.kind}</td><td className="p-2">{e.origin}</td><td className="p-2">{e.execution}</td></tr>)}</tbody>
      </table>
    </Card>
  </>;
}
