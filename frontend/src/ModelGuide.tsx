// Read the same offline learning catalog as REST/MCP. This view never loads a model.
import {useEffect, useState} from "react";
import type {Prediction} from "./types";

type Entry = {
  id: string; title: string; summary: string; good_at: string[]; caveats: string[];
  source_ids: string[]; local_recommendation: string;
  languages: {primary: string; coverage: string};
  identity: {repository: string; subfolder: string | null; revision: string; license: string; knowledge_cutoff: string};
  architecture: {backbone: string; parameters_approx_millions: number; encoder_layers: number; hidden_size: number; attention_heads: number; vocabulary_size: number; decision_head_layers: number; weights_bytes: number; cuda_autocast: string; stored_tensor_dtypes: string[]; parameter_note: string};
  tokens: {default_total: number; default_question: number; hosted_max_total: number; encoder_max_positions: number};
  upstream_evidence: {description: string; metrics: {name: string; value: number}[]};
  local_evidence: {quality: Record<string, {correct: number; count: number; macro_f1: number; review: number}>; service_ms: {median: number; p95: number}; http_ms: {median: number; p95: number}; batch: {states_per_second: number}; fresh_process_first_service_ms: number; fresh_process_peak_allocated_bytes: number; method: string};
  example: Prediction;
};
type Catalog = {
  reviewed_at: string; schema_version: string; provenance: string;
  family: {description: string; training: string; question_types: {type: string; meaning: string; example: string}[]};
  service: {routing: string; device_policy: string; token_notes: string[]; confidence_notes: string[]; usage_tips: string[]; limits: Record<string, number>; unexposed_upstream_features: string[]; errors: string; privacy: string};
  models: Entry[]; sources: {id: string; title: string; url: string}[];
};
const tasks: Record<string, string> = {issue_lane: "Issue workflow", security_specialist: "Security topic", qa_cause: "QA cause"};
function Notes({items}: {items: string[]}) {
  return <ul className="learning-list">{items.map(item => <li key={item}>{item}</li>)}</ul>;
}
function Specs({rows}: {rows: [string, string | number][]}) {
  return <dl className="learning-specs">{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}
function BudgetExplorer({model, notes}: {model: Entry; notes: string[]}) {
  const [total, setTotal] = useState(model.tokens.default_total);
  const [head, setHead] = useState(model.tokens.default_question);
  const valid = Number.isInteger(total) && Number.isInteger(head) && total >= 64 && total <= model.tokens.hosted_max_total && head >= 16 && head <= 1024 && head < total - 8;
  return <section className="learning-panel" aria-labelledby="budget-heading">
    <div className="learning-eyebrow">TOKENS · LOCAL EXPLORER</div><h2 id="budget-heading">How much evidence fits?</h2>
    <p>The full sequence includes the state, question, choices and formatting. Tokens are pieces of text; JSON keys and punctuation count too.</p>
    <div className="budget-controls">
      <label>Total context · max_len<input aria-label="Total token budget" type="number" min={64} max={model.tokens.hosted_max_total} value={total} onChange={e => setTotal(Number(e.target.value))}/></label>
      <label>Question + choices · head_max_len<input aria-label="Question token budget" type="number" min={16} max={1024} value={head} onChange={e => setHead(Number(e.target.value))}/></label>
    </div>
    {valid ? <><div className="budget-track" aria-hidden="true"><span className="budget-head" style={{width: `${head / total * 100}%`}}/><span className="budget-state" style={{width: `${(total - head) / total * 100}%`}}/></div><div className="budget-legend"><span>Question/options: {head.toLocaleString()}</span><strong>State: ≈ {(total - head).toLocaleString()} before formatting</strong></div></> : <p role="alert" className="learning-caution">Use integer budgets within this model's limits. The question budget must be less than total context minus eight.</p>}
    <p className="learning-footnote">This is a budget illustration, not tokenization of your input. Actual state room varies. A large limit does not guarantee accurate long-document decisions or enough GPU memory.</p>
    <Specs rows={[["Hosted maximum", `${model.tokens.hosted_max_total.toLocaleString()} tokens`], ["Encoder positions", `${model.tokens.encoder_max_positions.toLocaleString()} · separate from hosted limit`], ["Generated output tokens", "0 · typed answer only"]]}/>
    <details><summary>Truncation and option budgets</summary><Notes items={notes}/><p>Each option description is capped at 48 tokens before the shared head budget. About 20 choices or fewer is a quality recommendation; the 100-choice API limit is only validation.</p></details>
  </section>;
}

export default function ModelGuide({selected, select, useExample}: {selected: string; select: (model: string) => void; useExample: (request: Prediction, title: string) => void}) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch("/models.json", {signal: controller.signal}).then(async response => {
      if (!response.ok) throw new Error("Model catalog is unavailable. Refresh after the server starts.");
      return response.json() as Promise<Catalog>;
    }).then(setCatalog).catch(e => {if (e.name !== "AbortError") setError(e.message);});
    return () => controller.abort();
  }, []);
  useEffect(() => setCopied(false), [selected]);
  if (error) return <p className="alert" role="alert">{error}</p>;
  if (!catalog) return <p role="status">Loading the offline model guide…</p>;
  const model = catalog.models.find(m => m.id === selected) || catalog.models[0];
  const a = model.architecture, ev = model.local_evidence;
  const request = {...model.example, max_len: model.tokens.default_total, head_max_len: model.tokens.default_question};
  return <div className="model-learning">
    <div className="learning-topline"><span>Reviewed {catalog.reviewed_at} · offline catalog v{catalog.schema_version}</span><div><a href="/docs/models.md">Markdown for agents</a><a href="/models.json">JSON metadata</a></div></div>
    <p className="learning-footnote">No API key is needed to read this guide. Connect only when you want to run a prediction.</p>
    <p className="learning-intro">{catalog.family.description}</p>
    <div className="learning-selectors" role="group" aria-label="Choose a checkpoint to learn about">{catalog.models.map(m => <button key={m.id} className={`learning-selector ${model.id === m.id ? "selected" : ""}`} aria-pressed={model.id === m.id} onClick={() => select(m.id)}><span>{m.title}</span><small>{m.architecture.parameters_approx_millions}M · {m.tokens.default_total.toLocaleString()} tokens by default</small></button>)}</div>
    <section className="learning-overview" aria-labelledby="model-learning-title"><div><div className="learning-eyebrow">{model.languages.primary.toUpperCase()} · {model.identity.license}</div><h2 id="model-learning-title">{model.title}: when to use it</h2><p>{model.summary}</p><Notes items={model.good_at}/><p>{model.languages.coverage}</p></div><div className="learning-recommendation"><span className="tiny-tag">ON YOUR RTX 4050</span><h3>Measured guidance</h3><p>{model.local_recommendation}</p><strong>{ev.service_ms.median} ms</strong><span>Warm median service time · compact inputs</span></div></section>
    <div className="learning-columns"><BudgetExplorer model={model} key={model.id} notes={catalog.service.token_notes}/><section className="learning-panel"><div className="learning-eyebrow">BEFORE USING IT</div><h2>Strengths have limits</h2><Notes items={model.caveats}/><p className="learning-caution">A high probability can be wrong. These models do not approve repairs, payments, permission changes or tool execution.</p><details><summary>Confidence fields and review</summary><Notes items={catalog.service.confidence_notes}/></details><details><summary>Question types</summary>{catalog.family.question_types.map(q => <div className="learning-primitive" key={q.type}><h3><code>{q.type}</code></h3><p>{q.meaning}</p><small>Example: {q.example}</small></div>)}</details></section></div>
    <section className="learning-panel"><div className="learning-eyebrow">LOCAL EVIDENCE · 2026-10-01</div><h2>What we actually measured</h2><div className="learning-table-scroll"><table className="learning-table"><thead><tr><th scope="col">Task</th><th scope="col">Reference matches</th><th scope="col">Macro F1</th><th scope="col">Required review</th></tr></thead><tbody>{Object.entries(ev.quality).map(([task, q]) => <tr key={task}><th scope="row">{tasks[task]}</th><td>{q.correct} / {q.count}</td><td>{q.macro_f1.toFixed(4)}</td><td>{q.review} / {q.count}</td></tr>)}</tbody></table></div><div className="learning-measurements"><div><span>Warm service p95</span><strong>{ev.service_ms.p95} ms</strong></div><div><span>HTTP median / p95</span><strong>{ev.http_ms.median} / {ev.http_ms.p95} ms</strong></div><div><span>32-state batch</span><strong>{ev.batch.states_per_second} states/s</strong></div><div><span>Fresh-process first call</span><strong>{(ev.fresh_process_first_service_ms / 1000).toFixed(2)} s</strong></div><div><span>Process allocator peak</span><strong>{(ev.fresh_process_peak_allocated_bytes / 1024 ** 3).toFixed(3)} GiB</strong></div></div><p className="learning-footnote">{ev.method} Measurements used 512 total / 192 head tokens on every checkpoint; they do not predict maximum-context latency or memory.</p></section>
    <div className="learning-columns"><section className="learning-panel"><h2>Try a question you can inspect</h2><p>This loads a request into Playground with an explicit checkpoint. Your saved default stays unchanged.</p><pre className="learning-json">{JSON.stringify(request, null, 2)}</pre><div className="learning-actions"><button className="primary" onClick={() => useExample(request, `${model.title} learning example`)}>Try {model.title} example</button><button className="secondary" onClick={async () => {try {await navigator.clipboard.writeText(JSON.stringify(request, null, 2)); setCopied(true);} catch {setCopied(false);}}}>{copied ? "Copied request" : "Copy request JSON"}</button></div></section>
      <section className="learning-panel"><h2>Architecture and provenance</h2><Specs rows={[["Backbone", a.backbone], ["Model parameters (approx.)", `${a.parameters_approx_millions}M`], ["Encoder / decision-head layers", `${a.encoder_layers} / ${a.decision_head_layers}`], ["Hidden size / attention heads", `${a.hidden_size} / ${a.attention_heads}`], ["Tokenizer vocabulary", a.vocabulary_size.toLocaleString()], ["Weight file", `${(a.weights_bytes / 1024 ** 2).toFixed(2)} MiB · excludes runtime memory`], ["Stored / CUDA autocast types", `${a.stored_tensor_dtypes.join(", ")} / ${a.cuda_autocast}`], ["Checkpoint", `${model.identity.repository} / ${model.identity.subfolder || "root"}`], ["Pinned revision", model.identity.revision], ["Knowledge cutoff", model.identity.knowledge_cutoff]]}/><p className="learning-footnote">{a.parameter_note}</p><details><summary>Published evidence · upstream claims</summary><p>{model.upstream_evidence.description}</p><ul className="learning-list">{model.upstream_evidence.metrics.map(m => <li key={m.name}>{m.name}: {m.value}</li>)}</ul><p>{catalog.family.training}</p><p>Upstream results use different data and hardware. They are separate from our local reference agreement.</p></details></section></div>
    <section className="learning-panel"><h2>Using the hosted API well</h2><p>{catalog.service.routing}</p><Notes items={catalog.service.usage_tips}/><details><summary>Service limits, privacy and SDK differences</summary><p>{catalog.service.device_policy}</p><Specs rows={Object.entries(catalog.service.limits).map(([k, v]) => [k.replaceAll("_", " "), v.toLocaleString()])}/><p>{catalog.service.errors}</p><p>{catalog.service.privacy}</p><p>Upstream features not exposed by this server:</p><Notes items={catalog.service.unexposed_upstream_features}/></details><details><summary>Fetch from an AI agent</summary><pre className="learning-json">{`GET ${location.origin}/models.json\nGET ${location.origin}/docs/models.md\n\nAuthenticated: GET /api/v1/models/${model.id}/metadata\nAuthorization: Bearer <LAYA_API_KEY>\n\nMCP tool: laya_model_info {"model":"${model.id}"}\nResources: laya://models, laya://model-guide`}</pre><p>Public learning metadata needs no key. Runtime, inference and MCP require your bearer key. Cloud agents need a network path to this PC.</p></details></section>
    <footer className="learning-sources"><h2>Sources and verification</h2><p>{catalog.provenance}</p><ul>{catalog.sources.filter(s => model.source_ids.includes(s.id) || ["sdk", "adoption", "structured", "benchmarks"].includes(s.id)).map(s => <li key={s.id}><a href={s.url} target="_blank" rel="noreferrer">{s.title}</a></li>)}</ul><details><summary>Complete metadata for {model.title}</summary><pre className="learning-json">{JSON.stringify(model, null, 2)}</pre></details></footer>
  </div>;
}
