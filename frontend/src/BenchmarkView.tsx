import { useEffect, useState } from "react";
import type { Prediction } from "./types";

type Quality = { correct: number; count: number; macro_f1: number; review: number; high_confidence_wrong: number };
type Example = {
  id: string; title: string; source: string; expected_label: string; reference_basis: string;
  prediction: Prediction;
  observations: Record<string, { label: string; confidence: number; matches_reference: boolean }>;
};
type Benchmark = {
  started_at: string; unique_decisions: number; repeats: number; dependency_groups: number;
  interpretation: string;
  models: Record<string, { quality: Record<string, Quality>; service_ms: { median: number; p95: number };
    batch: { states_per_second: number }; max_observed_allocated_bytes: number }>;
  examples: Example[];
};

export default function BenchmarkView({ connected, load, useExample }: {
  connected: boolean; load: () => Promise<Benchmark>; useExample: (p: Prediction, title: string) => void;
}) {
  const [data, setData] = useState<Benchmark | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    if (!connected) { setData(null); return; }
    load().then(value => { if (active) setData(value); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [connected]);
  if (!connected) return <section className="panel"><h2>Real GPU benchmark</h2><p>Connect your API key to see the private repository examples.</p></section>;
  if (error) return <p role="alert">{error}</p>;
  if (!data) return <p>Loading the recorded benchmark…</p>;
  return <div className="benchmark-view">
    <section className="panel">
      <h2>Your issues, your GPU</h2>
      <p>134 GhostShield issues + 99 TotalGuard issues + 7 QA observations. {data.unique_decisions} decision cases, repeated {data.repeats} times per checkpoint on the RTX 4050.</p>
      <p className="muted">Recorded {data.started_at.slice(0, 10)}. These are saved measurements; opening this view does not run inference.</p>
      <div className="table-scroll"><table className="benchmark-table"><thead><tr>
        <th>Checkpoint</th><th>Issue workflow</th><th>Security topic</th><th>QA cause</th><th>Median / p95</th><th>Batch states/s</th>
      </tr></thead><tbody>{Object.entries(data.models).map(([model, stats]) => <tr key={model}>
        <th>{model}</th>{["issue_lane", "security_specialist", "qa_cause"].map(task => <td key={task}>{stats.quality[task].correct} / {stats.quality[task].count}</td>)}
        <td>{stats.service_ms.median} / {stats.service_ms.p95} ms</td><td>{stats.batch.states_per_second}</td>
      </tr>)}</tbody></table></div>
      <p>“Always dependency update” already matches 196 / 233 issues (84.1%). The seven QA cases include repeated failures across two days, so they are a small evidence audit.</p>
      <p className="benchmark-caution">{data.interpretation}</p>
      <p>196 dependency findings form {data.dependency_groups} repository/package work groups. Grouping organizes investigation; it does not resolve vulnerabilities.</p>
    </section>
    <section className="panel"><h2>Examples you can try</h2><p>Load an original benchmark input, choose a checkpoint in Playground, and compare its probabilities with the evidence reference.</p></section>
    <div className="benchmark-examples">{data.examples.map(example => <section className="panel" key={example.id}>
      <span className="tiny-tag">{example.id}</span><h3>{example.title}</h3>
      <p>Evidence reference: <strong>{example.expected_label}</strong></p><p className="muted">{example.reference_basis}</p>
      <ul>{Object.entries(example.observations).map(([model, value]) => <li key={model}>
        {model}: <strong>{value.label}</strong> · {(100 * value.confidence).toFixed(1)}% probability · {value.matches_reference ? "matches" : "misses"} reference
      </li>)}</ul>
      <div className="toolbar"><button className="primary" onClick={() => useExample(example.prediction, example.title)}>Try this example</button>
        <a href={example.source} target="_blank" rel="noreferrer">Original evidence ↗</a></div>
    </section>)}</div>
  </div>;
}
