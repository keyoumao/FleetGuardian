# FleetGuardian

The control room for representation-sensitive agent-security evaluations. SchemaShift measures committed ASR across tool-name and description variants under a frozen policy and adversarial objective. FleetGuardian presents the evidence, canonical comparisons, and recorded execution outcomes.

**Clean Semgrep ≠ honest security score.** Semgrep is the secondary harness source-trust module. Runtime fleet controls remain a labeled simulation. Bundled ASR results are synthetic fixtures, not measured schema effects.

See [web setup and evidence publishing](web/README.md).

## Automated ASR evidence

The home page now displays the completed 40-call GPT-4.1 mini experiment and its event-driven audit log. Three mock telemetry events triggered four schemas × five live trials × two separate executor conditions. Every variant had 0/5 attempted and committed attacks; no schema delta or boundary reduction was observed. This evaluates the fixed records-assistant contract, not the registered frontend source code.

The backend `runtime_agent.py` publishes `schema-audit.json`, `boundary-audit.json`, and `runtime-audit.json` together after validation. The runtime panel rejects a mismatched reference trace hash. The `/runtime` fleet screen remains a separate simulation. See the backend `RUNTIME.md` for replay commands and limitations.

### Revision comparison demo

On Representation ASR, choose **Revision demo · simulated**. Use **Simulate next MR** to advance one change or **Play scenario** for the full sequence: 20% reference → 60% wording regression → 30% neutral wording → 0% boundary-enforced commits. Every value is computed from explicit scripted counts (40 fixture trials per revision); identifiers and code diffs are fictional. The final revision retains 12 attempts and shows 12 blocks. Select any revealed revision to inspect its parent delta and per-schema counts; Reset restarts playback.

This demo neither pushes code nor runs a GitHub webhook, model, or MR check. The measured 40-call experiment remains unchanged in **Measured evidence**. Real revision comparisons require matched base/head evaluations and separate execution conditions before publishing an observed delta.

### Live security monitor

`/monitor` reads persisted security events from the backend's separate loopback service on port 8766 and refreshes every two seconds. Start it with `.venv/bin/python -m monitoring.api --db runs/monitor.sqlite3` in SchemaShiftAuditor. Critical incidents appear in a local inbox with provenance, execution mode, run IDs, and saved JSON logs. Test drills and historical replays are explicitly labeled. Collector failures show a disconnected state; saved results are not presented as a current connection. External notifications are disabled. This integration is local only and has not been deployed to the public Akash instance.
