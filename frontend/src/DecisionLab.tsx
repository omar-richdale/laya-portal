// Replay the frozen everyday study through the shared API; warm-ups never enter accuracy or latency summaries.
import { useEffect, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowRight, faBolt, faCheck, faDownload, faFlask, faLayerGroup, faStop, faClock, faChartSimple } from "@fortawesome/free-solid-svg-icons";
import type { Result } from "./types";
import { checkpoints, checkpointNames, exportJson, observed, stats } from "./labMetrics";
import type { Api, Catalog, Checkpoint, Observation, Replay } from "./labMetrics";

const percent = (n: number | null) => n === null ? "—" : `${(n * 100).toFixed(1)}%`;
const ms = (n: number | null | undefined) => n == null ? "—" : `${n.toFixed(1)} ms`;
const icon = (value: typeof faBolt) => <FontAwesomeIcon icon={value} aria-hidden="true" />;

export default function DecisionLab({ connected, busy, api, setBusy, onComplete }: {
  connected: boolean; busy: boolean; api: Api; setBusy: (value: boolean) => void; onComplete: () => void;
}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [selectedModels, setSelectedModels] = useState<Checkpoint[]>([...checkpoints]);
  const [selectedTasks, setSelectedTasks] = useState<string[]>([]);
  const [source, setSource] = useState<"saved" | "live">("saved");
  const [live, setLive] = useState<Replay | null>(null);
  const [running, setRunning] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [progress, setProgress] = useState({ completed: 0, total: 0, stage: "" });
  const [detailTask, setDetailTask] = useState("model_routing");
  const [detailModel, setDetailModel] = useState<Checkpoint>("typed-decisions");
  const [filter, setFilter] = useState("all");
  const stop = useRef(false);
  const inFlight = useRef(false);

  useEffect(() => {
    let active = true;
    if (!connected) { stop.current = true; return; }
    setError("");
    api<Catalog>("/api/v1/decision-suite").then(data => {
      if (active) { setCatalog(data); setSelectedTasks(data.tasks.map(t => t.id)); }
    }).catch(e => { if (active) setError((e as Error).message); });
    return () => { active = false; stop.current = true; };
  }, [connected]);

  async function run() {
    if (!catalog || inFlight.current || !selectedModels.length || !selectedTasks.length) return;
    inFlight.current = true; stop.current = false;
    setRunning(true); setBusy(true); setStopping(false); setError(""); setSource("live");
    const tasks = catalog.tasks.filter(t => selectedTasks.includes(t.id));
    const total = tasks.reduce((n, t) => n + t.cases.length, 0) * selectedModels.length;
    const replay: Replay = { created_at: new Date().toISOString(), fixture_sha256: catalog.fixture_sha256, request_sha256: catalog.request_sha256,
      models: [...selectedModels], records: [], warmups: [], status: "running" };
    setLive({ ...replay });
    setDetailTask(tasks[0].id); setDetailModel(selectedModels[0]); setFilter("all");
    setProgress({ completed: 0, total, stage: "Starting replay…" });
    try {
      for (const model of selectedModels) {
        if (stop.current) break;
        setProgress(p => ({ ...p, stage: `Warming ${checkpointNames[model]}…` }));
        const warm = await api<Result>("/api/v1/predict", { ...tasks[0].cases[0].prediction, model });
        replay.warmups.push({ model, service_ms: warm.runtime.elapsed_ms, load_ms: warm.runtime.load_ms });
        setLive({ ...replay, records: [...replay.records], warmups: [...replay.warmups] });
        for (const task of tasks) {
          for (const item of task.cases) {
            if (stop.current) break;
            setProgress(p => ({ ...p, stage: `${checkpointNames[model]} · ${task.title}` }));
            const start = performance.now();
            const response = await api<Result>("/api/v1/predict", { ...item.prediction, model });
            replay.records.push(observed(response, model, task, item, performance.now() - start));
            setLive({ ...replay, records: [...replay.records], warmups: [...replay.warmups] });
            setProgress(p => ({ ...p, completed: replay.records.length }));
          }
          if (stop.current) break;
        }
      }
      replay.status = stop.current ? "stopped" : "completed";
      setProgress(p => ({ ...p, stage: stop.current ? "Stopped · completed results retained" : "Replay complete" }));
    } catch (e) {
      replay.status = "failed";
      setError((e as Error).message);
      setProgress(p => ({ ...p, stage: "Replay interrupted · completed results retained" }));
    } finally {
      setLive({ ...replay, records: [...replay.records], warmups: [...replay.warmups] });
      inFlight.current = false;
      setRunning(false); setBusy(false); setStopping(false); onComplete();
    }
  }

  if (!connected) return <section className="lab-empty panel"><h2>Decision lab</h2><p>Connect your API key to explore the saved comparison and replay the built-in tests.</p></section>;
  if (!catalog) return <section className="lab-empty panel"><h2>Decision lab</h2><p role={error ? "alert" : "status"}>{error || "Loading the six test suites…"}</p></section>;

  const shown = source === "saved" ? catalog.baseline : live;
  const rows = shown?.records || [];
  const all = stats(rows, catalog.tasks);
  const task = catalog.tasks.find(t => t.id === detailTask) || catalog.tasks[0];
  const taskRows = rows.filter(r => r.task === task.id && r.model === detailModel);
  const breakdown = stats(taskRows, [task]);
  const totalCases = catalog.tasks.reduce((n, t) => n + t.cases.length, 0);
  const runCases = catalog.tasks.filter(t => selectedTasks.includes(t.id)).reduce((n, t) => n + t.cases.length, 0) * selectedModels.length;
  const getCase = (row: Observation) => task.cases.find(c => c.id === row.case_id)!;
  const isMatch = (row: Observation) => row.valid && row.choice === getCase(row).expected;
  const filtered = taskRows.filter(r => filter === "all" || (filter === "misses" && !isMatch(r)) || (filter === "matches" && isMatch(r)) || (filter === "uncertain" && r.confidence < 0.8));
  const warnings = [...new Set(rows.flatMap(r => r.warnings))];
  const toggleModel = (model: Checkpoint) => setSelectedModels(current => current.includes(model) ? current.filter(m => m !== model) : checkpoints.filter(m => [...current, model].includes(m)));
  const toggleTask = (id: string) => setSelectedTasks(current => current.includes(id) ? current.filter(t => t !== id) : [...current, id]);

  return <div className="decision-lab">
    <section className="lab-intro">
      <div><span className="lab-eyebrow">{icon(faFlask)} EVERYDAY DECISION LAB</span><h2>Know what it’s good at<span>.</span></h2>
        <p>Six practical suites. Three checkpoints. One clear comparison of every decision.</p>
        <div className="lab-tags"><span>{totalCases} labeled cases</span><span>English prompts</span><span>Local GPU replay</span></div></div>
      <div className="lab-orbit" aria-hidden="true"><span>01</span>{icon(faChartSimple)}<span>130</span></div>
    </section>

    <div className="lab-kpis">
      <div><span>Scored predictions</span><strong>{rows.length || "—"}</strong><small>{source === "saved" ? "Recorded comparison" : shown?.status === "completed" ? "Completed live run" : "Live run · partial results"}</small></div>
      <div><span>Reference accuracy</span><strong>{percent(all.accuracy)}</strong><small>{all.matches} matching labels / {all.count} decisions</small></div>
      <div><span>Warm inference median</span><strong>{ms(all.median)}</strong><small>GPU service time · warm-ups excluded</small></div>
      <div><span>Confident errors</span><strong>{all.confidentErrors}</strong><small>{all.confident} decisions at ≥80% confidence</small></div>
    </div>

    <section className="lab-runner panel">
      <div className="lab-heading"><div><h3>Build your comparison</h3><p>Choose the tasks and checkpoints to replay.</p></div><span className="lab-chip">{runCases} predictions + {selectedModels.length} warm-ups</span></div>
      <div className="lab-models" role="group" aria-label="Checkpoints to test">{checkpoints.map(model => <label key={model} className={selectedModels.includes(model) ? "selected" : ""}>
        <input type="checkbox" checked={selectedModels.includes(model)} disabled={running || busy} onChange={() => toggleModel(model)} />
        <span className={`lab-model-dot ${model}`} />{checkpointNames[model]}</label>)}</div>
      <div className="lab-suites">{catalog.tasks.map(t => <label key={t.id} className={selectedTasks.includes(t.id) ? "selected" : ""}>
        <input type="checkbox" checked={selectedTasks.includes(t.id)} disabled={running || busy} onChange={() => toggleTask(t.id)} aria-label={`Include ${t.title}`} />
        <div><strong>{t.title}</strong><p>{t.description}</p></div><span>{t.cases.length}</span></label>)}</div>
      <div className="lab-run-actions"><p>{icon(faClock)} Loading a checkpoint can take longer than a warm prediction.</p>
        {running ? <button className="secondary" disabled={stopping} onClick={() => { stop.current = true; setStopping(true); }}>{icon(faStop)} {stopping ? "Stopping after current request…" : "Stop after current request"}</button> :
          <button className="primary" disabled={busy || !runCases} onClick={() => void run()}>{icon(faBolt)} Run selected tests</button>}</div>
      {(running || live) && <div className="lab-progress" aria-live="polite"><div><span>{progress.stage}</span><strong>{progress.completed} / {progress.total}</strong></div><progress value={progress.completed} max={progress.total || 1} aria-label="Decision lab progress" /></div>}
      {error && <p role="alert" className="lab-error">{error}</p>}
    </section>

    <section className="panel lab-comparison">
      <div className="lab-heading"><div><h3>Checkpoint comparison</h3><p>{source === "saved" ? `Recorded ${catalog.baseline.created_at.slice(0, 10)} · ${catalog.baseline.environment?.gpu}` : live ? `Live replay · ${live.status} · ${new Date(live.created_at).toLocaleString()}` : "Run a suite to collect fresh measurements."}</p></div>
        <div className="lab-view-actions"><div className="lab-segment" aria-label="Result source"><button aria-pressed={source === "saved"} onClick={() => setSource("saved")}>Saved comparison</button><button aria-pressed={source === "live"} disabled={!live} onClick={() => setSource("live")}>Latest run</button></div>
          <button className="text-button" disabled={!shown || !rows.length} onClick={() => exportJson("laya-decision-lab-results.json", { ...shown, references: catalog.tasks, fixture_sha256: catalog.fixture_sha256 })}>{icon(faDownload)} Export results</button></div></div>
      <div className="lab-table-wrap"><table className="lab-comparison-table"><caption>Reference-label accuracy and median warm service time. Select a result to inspect its decisions.</caption><thead><tr><th scope="col">Test suite</th>{checkpoints.map(m => <th scope="col" key={m}><span className={`lab-model-dot ${m}`} />{checkpointNames[m]}</th>)}</tr></thead>
        <tbody>{catalog.tasks.map(t => <tr key={t.id}><th scope="row"><strong>{t.title}</strong><small>{t.cases.length} cases · {Object.keys(t.criteria).length} labels</small></th>{checkpoints.map(m => {
          const s = stats(rows.filter(r => r.task === t.id && r.model === m), [t]);
          return <td key={m}><button className="lab-score" aria-label={`Inspect ${t.title}, ${checkpointNames[m]}`} onClick={() => { setDetailTask(t.id); setDetailModel(m); setFilter("all"); }}>
            <div><strong>{percent(s.accuracy)}</strong><span>{s.count ? `${s.matches}/${s.count}` : "No results"}</span></div><div className="lab-score-track"><i style={{ width: `${(s.accuracy || 0) * 100}%` }} /></div><small>{ms(s.median)} <span>median {icon(faArrowRight)}</span></small></button></td>;
        })}</tr>)}</tbody></table></div>
      <p className="lab-footnote">Accuracy means matching the supplied reference labels. This is a small synthetic study with custom moderation policies, not production accuracy. Image and video tests classify prompts only.</p>
    </section>

    <section className="panel lab-timing"><div className="lab-heading"><div><h3>Where the time goes</h3><p>Warm decisions, request overhead and initial checkpoint warm-up.</p></div></div>
      <div className="lab-table-wrap"><table className="lab-data-table"><caption>Timing and confidence across the results currently shown</caption><thead><tr><th>Checkpoint</th><th>Median inference</th><th>p95 inference</th><th>Median HTTP</th><th>Initial warm-up</th><th>≥80% coverage</th><th>Confident errors</th></tr></thead><tbody>{checkpoints.map(m => {
        const s = stats(rows.filter(r => r.model === m), catalog.tasks);
        const warm = shown?.warmups.find(w => w.model === m);
        return <tr key={m}><th>{checkpointNames[m]}</th><td>{ms(s.median)}</td><td>{ms(s.p95)}</td><td>{ms(s.httpMedian)}</td><td>{ms(warm?.service_ms)}</td><td>{s.confident}/{s.count}</td><td>{s.confidentErrors}</td></tr>;
      })}</tbody></table></div><p className="lab-footnote">Initial warm-up includes any loading and one excluded prediction. Service time measures the worker; HTTP time includes the request round trip. Confidence is not a guarantee of correctness.</p></section>

    <section className="panel lab-details"><div className="lab-heading"><div><h3>Inside every decision</h3><p>Inspect the prompt, reference, prediction and confidence.</p></div><div className="lab-detail-selects"><label>Suite<select aria-label="Inspect suite" value={task.id} onChange={e => { setDetailTask(e.target.value); setFilter("all"); }}>{catalog.tasks.map(t => <option key={t.id} value={t.id}>{t.title}</option>)}</select></label><label>Checkpoint<select aria-label="Inspect checkpoint" value={detailModel} onChange={e => setDetailModel(e.target.value as Checkpoint)}>{checkpoints.map(m => <option key={m} value={m}>{checkpointNames[m]}</option>)}</select></label></div></div>
      <div className="lab-detail-metrics"><span><strong>{breakdown.matches}/{breakdown.count}</strong> reference matches</span><span><strong>{breakdown.confidentErrors}</strong> confident errors</span><span><strong>{breakdown.incomplete}</strong> incomplete results</span>{task.id.includes("moderation") && <><span><strong>{breakdown.unsafeAllows}</strong> block → allow</span><span><strong>{breakdown.benignBlocks}</strong> allow → block</span><span><strong>{breakdown.referrals}</strong> sent to review</span></>}</div>
      <details className="lab-policy"><summary>Policy, labels and confusion table</summary><p>{task.policy}</p><div className="lab-confusion-layout"><dl>{Object.entries(task.criteria).map(([label, description]) => <div key={label}><dt>{label}</dt><dd>{description}</dd></div>)}</dl><div className="lab-table-wrap"><table className="lab-confusion"><caption>Rows: reference · columns: prediction</caption><thead><tr><th>Reference ↓</th>{Object.keys(task.criteria).map(label => <th key={label}>{label}</th>)}</tr></thead><tbody>{Object.keys(task.criteria).map(expected => <tr key={expected}><th>{expected}</th>{Object.keys(task.criteria).map(predicted => {
        const count = taskRows.filter(r => r.valid && getCase(r).expected === expected && r.choice === predicted).length;
        return <td key={predicted} className={count ? expected === predicted ? "diagonal" : "off-diagonal" : ""}>{count}</td>;
      })}</tr>)}</tbody></table></div></div></details>
      <div className="lab-case-toolbar"><label>Show<select aria-label="Filter decisions" value={filter} onChange={e => setFilter(e.target.value)}><option value="all">All decisions</option><option value="misses">Mismatches</option><option value="matches">Matches</option><option value="uncertain">Below 80% confidence</option></select></label><button className="text-button" onClick={() => exportJson(`laya-${task.id}-${detailModel}-requests.json`, task.cases.map(c => ({ ...c.prediction, model: detailModel })))}>{icon(faDownload)} Export suite requests</button></div>
      <div className="lab-table-wrap lab-case-scroll"><table className="lab-case-table"><caption>{filtered.length} decisions shown for {task.title} · {checkpointNames[detailModel]}</caption><thead><tr><th>Case / prompt</th><th>Reference</th><th>Decision</th><th>Confidence</th><th>Inference / HTTP</th><th>Result</th></tr></thead><tbody>{filtered.map(r => <tr key={r.case_id}><td><details><summary><span className="lab-case-number">{r.case_id.split("-").at(-1)}</span>{getCase(r).prompt}</summary><pre>{JSON.stringify({ request: { ...getCase(r).prediction, model: r.model }, probabilities: r.probabilities, usage: r.usage, device: r.device, warnings: r.warnings }, null, 2)}</pre></details></td><td><span className="lab-label">{getCase(r).expected}</span></td><td><span className="lab-label">{r.choice}</span></td><td>{percent(r.confidence)}{r.confidence < 0.8 && <small className="lab-uncertain">Below threshold</small>}</td><td>{ms(r.service_ms)}<small>{ms(r.http_ms)} HTTP</small></td><td><span className={`lab-outcome ${isMatch(r) ? "match" : "miss"}`}>{isMatch(r) ? icon(faCheck) : "×"} {r.valid ? isMatch(r) ? "Match" : "Mismatch" : "Incomplete"}</span></td></tr>)}</tbody></table>{!filtered.length && <p className="lab-no-results">{taskRows.length ? "No decisions match this filter." : "No results yet for this suite and checkpoint."}</p>}</div>
    </section>

    <details className="lab-method panel"><summary>{icon(faLayerGroup)} Method and reproducibility</summary><p>The {totalCases} author-labeled cases are balanced within each suite and were fixed before the recorded study. Reference labels are excluded from model inputs. Replays use one request at a time on the shared GPU worker, with one excluded warm-up per checkpoint. Explicit checkpoint selection preserves the saved default.</p><p>Stopped or failed runs show only completed requests. Truncated or misrouted results are marked incomplete and never count as matches. Live results remain available while this page is open; export them to keep a copy.</p><p className="lab-hash">Fixture SHA-256: {catalog.fixture_sha256}</p><p className="lab-hash">Request SHA-256 (including option order): {catalog.request_sha256}</p>{warnings.length > 0 && <div className="lab-warnings"><strong>Runtime notices</strong>{warnings.map(w => <p key={w}>{w}</p>)}</div>}</details>
  </div>;
}
