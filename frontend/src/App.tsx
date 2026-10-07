// Dashboard state stays in this tab. All predictions go to the shared Python worker.
import { useEffect, useState, type ReactNode } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faArrowRight,
  faBolt,
  faBookOpen,
  faCheck,
  faCode,
  faCopy,
  faCube,
  faDownload,
  faFlask,
  faGear,
  faKey,
  faLayerGroup,
  faMicrochip,
  faPlus,
  faRotate,
  faTerminal,
  faTrash,
  faUpload,
} from "@fortawesome/free-solid-svg-icons";
import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import SpotlightCard from "./vendor/SpotlightCard";
import FadeContent from "./vendor/FadeContent";
import { presets } from "./presets";
import BenchmarkView from "./BenchmarkView";
import ModelGuide from "./ModelGuide";
import type {
  Model,
  ModelInfo,
  Prediction,
  Question,
  Result,
  Runtime,
} from "./types";

const pretty = (value: unknown) => JSON.stringify(value, null, 2);
const choices: Model[] = ["auto", "english", "multilingual", "typed-decisions"];
const names: Record<string, string> = {
  auto: "Automatic routing",
  english: "English",
  multilingual: "Multilingual",
  "typed-decisions": "Typed decisions",
};
function Icon({ icon }: { icon: IconDefinition }) {
  return <FontAwesomeIcon icon={icon} aria-hidden="true" />;
}
function download(name: string, value: unknown) {
  const url = URL.createObjectURL(
    new Blob([pretty(value)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}
function ModelSelect({
  value,
  onChange,
  defaultOption = false,
}: {
  value: string;
  onChange: (v: string) => void;
  defaultOption?: boolean;
}) {
  return (
    <select
      aria-label="Request model"
      value={value}
      onChange={(e) => onChange(e.target.value)}
    >
      {defaultOption && <option value="">Service default</option>}
      {choices.map((m) => (
        <option key={m} value={m}>
          {names[m]}
        </option>
      ))}
    </select>
  );
}
function Panel({
  title,
  description,
  children,
  tools,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  tools?: ReactNode;
}) {
  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>{title}</h2>
          {description && <p>{description}</p>}
        </div>
        {tools}
      </div>
      {children}
    </section>
  );
}

export default function App() {
  const [tab, setTab] = useState(() => location.pathname === "/model-guide" ? "model-guide" : "playground");
  const [guideModel, setGuideModel] = useState(() => ["english", "multilingual", "typed-decisions"].includes(location.hash.slice(1)) ? location.hash.slice(1) : "english");
  const [key, setKey] = useState(
    () => sessionStorage.getItem("laya-key") || "",
  );
  const [keyDraft, setKeyDraft] = useState("");
  const [status, setStatus] = useState<Runtime | null>(null);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [connected, setConnected] = useState(false);
  const [stateText, setStateText] = useState(
    String(presets["Support triage"].state),
  );
  const [stateMode, setStateMode] = useState("text");
  const [questionText, setQuestionText] = useState(
    pretty(presets["Support triage"].questions),
  );
  const [questionMode, setQuestionMode] = useState("form");
  const [model, setModel] = useState("");
  const [context, setContext] = useState("");
  const [head, setHead] = useState("");
  const [threshold, setThreshold] = useState("");
  const [result, setResult] = useState<Result | null>(null);
  const [resultQuestions, setResultQuestions] = useState<Record<string, Question>>({});
  const [raw, setRaw] = useState(false);
  const [batchText, setBatchText] = useState(
    pretty([
      presets["Support triage"],
      presets["French support"],
      presets["Arabic support"],
    ]),
  );
  const [batchResult, setBatchResult] = useState<{
    results: Result[];
    runtime: { elapsed_ms: number };
  } | null>(null);
  const [microbatch, setMicrobatch] = useState(2);
  const [reduced, setReduced] = useState(
    () => window.matchMedia("(prefers-reduced-motion: reduce)").matches,
  );

  async function api<T>(
    path: string,
    body?: unknown,
    method = "POST",
  ): Promise<T> {
    const response = await fetch(path, {
      method: body === undefined ? "GET" : method,
      headers: {
        Authorization: `Bearer ${key}`,
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      const e = data.error;
      throw new Error(
        `${e?.message || "Request failed"}${e?.details ? " — " + e.details.map((x: { loc: string[]; message: string }) => x.loc.join(".") + ": " + x.message).join("; ") : ""}${response.headers.has("Retry-After") ? " Retry after " + response.headers.get("Retry-After") + " seconds." : ""}`,
      );
    }
    return data as T;
  }
  async function refresh() {
    if (!key) return;
    try {
      const [runtime, listing] = await Promise.all([
        api<Runtime>("/api/v1/status"),
        api<{ models: ModelInfo[] }>("/api/v1/models"),
      ]);
      setStatus(runtime);
      setModels(listing.models);
      setConnected(true);
    } catch (e) {
      setConnected(false);
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    sessionStorage.setItem("laya-key", key);
    setError("");
    void refresh();
    const timer = setInterval(() => void refresh(), 4000);
    return () => clearInterval(timer);
  }, [key]);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const listener = () => setReduced(media.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);
  const working =
    busy || ["loading", "inferencing"].includes(status?.phase || "");
  let questions: Record<string, Question> = {};
  let invalidQuestionForm = false;
  try {
    const parsed = JSON.parse(questionText);
    if (
      !parsed ||
      Array.isArray(parsed) ||
      typeof parsed !== "object" ||
      !Object.values(parsed).every((entry) => {
        const q = entry as Question;
        return (
          q &&
          typeof q.instructions === "string" &&
          ["choice", "score", "noul"].includes(q.type) &&
          (q.type === "noul" ||
            (q.type === "score"
              ? Array.isArray(q.criteria)
              : q.criteria &&
                typeof q.criteria === "object" &&
                !Array.isArray(q.criteria)))
        );
      })
    )
      throw new Error("Invalid question form");
    questions = parsed;
  } catch {
    invalidQuestionForm = true;
  }
  function editQuestions(next: Record<string, Question>) {
    setQuestionText(pretty(next));
  }
  function preset(name: string) {
    const p = presets[name];
    setStateMode(typeof p.state === "string" ? "text" : "json");
    setStateText(typeof p.state === "string" ? p.state : pretty(p.state));
    setQuestionText(pretty(p.questions));
    setModel(p.model || "");
    setResult(null);
    setError("");
  }
  function payload(): Prediction {
    return {
      state: stateMode === "json" ? JSON.parse(stateText) : stateText,
      questions: JSON.parse(questionText),
      ...(model ? { model: model as Model } : {}),
      ...(context ? { max_len: Number(context) } : {}),
      ...(head ? { head_max_len: Number(head) } : {}),
      ...(threshold ? { min_confidence: Number(threshold) } : {}),
    };
  }
  async function run() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const request = payload();
      const response = await api<Result>("/api/v1/predict", request);
      setResultQuestions(request.questions);
      setResult(response);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      void refresh();
    }
  }
  async function runBatch() {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      let requests: Prediction[];
      try {
        const parsed = JSON.parse(batchText);
        requests = Array.isArray(parsed) ? parsed : parsed.requests;
      } catch {
        requests = batchText
          .split("\n")
          .filter((x) => x.trim())
          .map((x) => JSON.parse(x));
      }
      setBatchResult(
        await api("/api/v1/predict/batch", {
          requests,
          batch_size: microbatch,
          sort_by_length: true,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      void refresh();
    }
  }
  async function defaultModel(value: Model) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await api("/api/v1/settings/model", { model: value }, "PUT");
      setNotice(`${names[value]} is now the saved service default.`);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setNotice("Copied to clipboard.");
    } catch {
      setError(
        "Clipboard is unavailable over this connection. Use localhost or export the request.",
      );
    }
  }
  async function importBatch(file?: File) {
    if (file) setBatchText(await file.text());
  }
  const nav = [
    ["playground", "Playground", faFlask],
    ["batch", "Batch testing", faLayerGroup],
    ["models", "Models & GPU", faMicrochip],
    ["model-guide", "Model guide", faBookOpen],
    ["benchmark", "Real benchmark", faBolt],
    ["guide", "Integration", faCode],
  ] as const;

  return (
    <div className={`shell ${working ? "working" : ""}`}>
      <aside className="sidebar">
        <a className="brand" href="/" aria-label="Laya home">
          <span className="brand-mark">L</span>
          <span>
            laya<span className="brand-caption">SYSTEM ONE</span>
          </span>
        </a>
        <div className="workspace-label">
          LOCAL WORKSPACE <span>01</span>
        </div>
        <nav>
          {nav.map(([id, label, icon]) => (
            <button
              key={id}
              className={tab === id ? "nav-item active" : "nav-item"}
              onClick={() => {
                setTab(id);
                history.replaceState(null, "", id === "model-guide" ? `/model-guide#${guideModel}` : "/");
                setError("");
                setNotice("");
              }}
            >
              <Icon icon={icon} />
              {label}
              {tab === id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="tiny-tag">REFERENCE IMPLEMENTATION</span>
          <p>
            Python + PyTorch.
            <br />
            Your GPU. Your decisions.
          </p>
          <span className="offline-label">
            <i /> Local inference
          </span>
        </div>
        <div className="sidebar-footer">
          <a href="/llms.txt" target="_blank">
            Agent documentation <Icon icon={faArrowRight} />
          </a>
          <span>Laya Local · v0.1.0</span>
        </div>
      </aside>
      <main
        onKeyDown={(e) => {
          if (
            (e.ctrlKey || e.metaKey) &&
            e.key === "Enter" &&
            tab === "playground" &&
            connected &&
            !busy
          ) {
            e.preventDefault();
            void run();
          }
        }}
      >
        <header className="topbar">
          <span>
            <span className="muted">Workspace</span>
            <span className="slash">/</span>
            {nav.find((x) => x[0] === tab)?.[1]}
          </span>
          <div className="topbar-right">
            <span className="tag">
              <i className={connected ? "status-dot" : "status-dot dim"} />
              {connected ? "GPU service connected" : "Connect your API key"}
            </span>
            <button
              className="icon-button"
              aria-label="Refresh status"
              onClick={() => void refresh()}
            >
              <Icon icon={faRotate} />
            </button>
          </div>
        </header>
        <div className="content">
          <div className="hero">
            <div>
              <div className="eyebrow">
                <span /> THE LOCAL DECISION ENGINE
              </div>
              <h1>
                {tab === "playground" ? (
                  <>
                    Less waiting.
                    <br />
                    <span className="gradient-text">More deciding.</span>
                  </>
                ) : tab === "batch" ? (
                  <>
                    One batch.
                    <br />
                    <span className="gradient-text">Every decision.</span>
                  </>
                ) : tab === "models" ? (
                  <>
                    Three checkpoints.
                    <br />
                    <span className="gradient-text">One local GPU.</span>
                  </>
                ) : tab === "model-guide" ? (
                  <>Know your models.<br /><span className="gradient-text">Choose with evidence.</span></>
                ) : tab === "benchmark" ? (
                  <>Real evidence.<br /><span className="gradient-text">Measured decisions.</span></>
                ) : (
                  <>
                    Build with Laya.
                    <br />
                    <span className="gradient-text">Connect anything.</span>
                  </>
                )}
              </h1>
              <p>
                {tab === "playground"
                  ? "Turn text and structured data into typed decisions. Test questions, explore probabilities, and connect your apps."
                  : tab === "batch"
                    ? "Run a collection of requests through the same GPU worker. Review results in their original order."
                    : tab === "models"
                      ? "Choose the service default and inspect the device doing the work. Checkpoints load one at a time."
                      : tab === "model-guide"
                        ? "Learn each checkpoint's capabilities, token budgets and limits. Published claims and local GPU measurements are shown separately."
                      : tab === "benchmark"
                        ? "Compare all three checkpoints on your GitHub issues and QA failures, then try the same inputs yourself."
                        : "A documented HTTP API and MCP tools, backed by one local inference service."}
              </p>
            </div>
            <div className="hero-art" aria-hidden="true">
              <div className="orbit orbit-one" />
              <div className="orbit orbit-two" />
              <div className="decision-core">
                <Icon icon={faBolt} />
              </div>
              <span className="orbit-label">STATE → DECISION</span>
            </div>
          </div>
          <div className="metrics">
            {[
              [
                faMicrochip,
                "COMPUTE",
                status?.gpu?.name?.replace("NVIDIA GeForce ", "") || "RTX 4050",
                "CUDA · GPU only",
              ],
              [
                faCube,
                "DEFAULT MODEL",
                names[status?.default_model || "auto"],
                "Per-request overrides supported",
              ],
              [
                faBolt,
                "LAST REQUEST",
                result
                  ? `${result.runtime.elapsed_ms.toFixed(0)} ms`
                  : "Ready to test",
                result
                  ? names[result.routing.model]
                  : "Measured on this machine",
              ],
              [
                faLayerGroup,
                "GPU MEMORY",
                status?.gpu
                  ? `${(status.gpu.free_bytes / 1024 ** 3).toFixed(1)} GB free`
                  : "6 GB VRAM",
                "One resident checkpoint",
              ],
            ].map(([icon, label, value, sub]) => (
              <SpotlightCard
                key={String(label)}
                className="metric"
                spotlightColor="rgba(115, 89, 255, 0.13)"
              >
                <div className="metric-top">
                  <span>{String(label)}</span>
                  <Icon icon={icon as IconDefinition} />
                </div>
                <strong>{String(value)}</strong>
                <small>{String(sub)}</small>
              </SpotlightCard>
            ))}
          </div>
          {!key && (
            <div className="connect-panel">
              <span className="connect-icon">
                <Icon icon={faKey} />
              </span>
              <div>
                <h3>Connect to your local service</h3>
                <p>
                  Paste LAYA_API_KEY from this project’s .env file. It stays in
                  this tab.
                </p>
              </div>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setKey(keyDraft.trim());
                  setKeyDraft("");
                }}
              >
                <input
                  type="password"
                  aria-label="API key"
                  placeholder="Enter your API key"
                  value={keyDraft}
                  onChange={(e) => setKeyDraft(e.target.value)}
                  autoComplete="off"
                />
                <button className="primary small" disabled={!keyDraft.trim()}>
                  Connect <Icon icon={faArrowRight} />
                </button>
              </form>
            </div>
          )}
          {key && (
            <div className="connection-line">
              <span>
                <Icon icon={faKey} />{" "}
                {connected
                  ? "Authenticated for this tab"
                  : "Checking your API key…"}
              </span>
              <button
                className="text-button"
                onClick={() => {
                  setKey("");
                  setStatus(null);
                  setConnected(false);
                  sessionStorage.removeItem("laya-key");
                }}
              >
                Disconnect
              </button>
            </div>
          )}
          {error && (
            <div className="alert error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="alert success" role="status">
              <Icon icon={faCheck} /> {notice}
            </div>
          )}
          {working && (
            <div className="activity" role="status">
              <span className="spinner" />
              {status?.phase === "loading"
                ? `Loading ${names[status.loading_model || ""] || "checkpoint"} onto the GPU…`
                : "Running your request on the shared GPU worker…"}
            </div>
          )}
          {tab === "playground" && (
            <>
              <div className="section-toolbar">
                <div>
                  <h2>The playground</h2>
                  <p>
                    Define your input. Ask typed questions. Inspect the
                    decision.
                  </p>
                </div>
                <label className="preset-label">
                  START WITH AN EXAMPLE
                  <select
                    aria-label="Example preset"
                    defaultValue="Support triage"
                    onChange={(e) => preset(e.target.value)}
                  >
                    {Object.keys(presets).map((p) => (
                      <option key={p}>{p}</option>
                    ))}
                  </select>
                </label>
              </div>
              <div className="playground-grid">
                <div className="request-column">
                  <Panel
                    title="01 / State"
                    description="The text or JSON you want Laya to evaluate."
                    tools={
                      <div className="segmented">
                        {["text", "json"].map((m) => (
                          <button
                            key={m}
                            className={stateMode === m ? "selected" : ""}
                            onClick={() => setStateMode(m)}
                          >
                            {m.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    }
                  >
                    <textarea
                      className="state-editor"
                      aria-label="State input"
                      value={stateText}
                      onChange={(e) => setStateText(e.target.value)}
                      spellCheck={false}
                    />
                    <div className="editor-footer">
                      <span>
                        {stateText.length.toLocaleString()} characters
                      </span>
                      <span>Processed locally</span>
                    </div>
                  </Panel>
                  <Panel
                    title="02 / Questions"
                    description="Choices, ordinal scores, and yes/no probabilities."
                    tools={
                      <div className="segmented">
                        {["form", "json"].map((m) => (
                          <button
                            key={m}
                            className={questionMode === m ? "selected" : ""}
                            onClick={() => setQuestionMode(m)}
                          >
                            {m.toUpperCase()}
                          </button>
                        ))}
                      </div>
                    }
                  >
                    {questionMode === "json" ? (
                      <textarea
                        className="code-editor questions-json"
                        aria-label="Questions JSON"
                        value={questionText}
                        onChange={(e) => setQuestionText(e.target.value)}
                        spellCheck={false}
                      />
                    ) : invalidQuestionForm ? (
                      <p className="alert warning">
                        These questions cannot be shown as a form. Switch to
                        JSON to correct the question definitions.
                      </p>
                    ) : (
                      <div className="question-list">
                        {Object.entries(questions).map(([id, q], index) => (
                          <div className="question" key={id}>
                            <div className="question-top">
                              <span className="number">
                                {String(index + 1).padStart(2, "0")}
                              </span>
                              <strong>{id}</strong>
                              <select
                                aria-label={`${id} type`}
                                value={q.type}
                                onChange={(e) => {
                                  const type = e.target
                                    .value as Question["type"];
                                  editQuestions({
                                    ...questions,
                                    [id]: {
                                      type,
                                      instructions: q.instructions,
                                      ...(type === "choice"
                                        ? {
                                            criteria: {
                                              A: "First option",
                                              B: "Second option",
                                            },
                                          }
                                        : type === "score"
                                          ? {
                                              criteria: [
                                                "low",
                                                "medium",
                                                "high",
                                              ],
                                            }
                                          : {}),
                                    },
                                  });
                                }}
                              >
                                <option value="choice">Choice</option>
                                <option value="score">Score</option>
                                <option value="noul">Yes / No</option>
                              </select>
                              <button
                                aria-label={`Remove ${id}`}
                                className="icon-button"
                                onClick={() => {
                                  const next = { ...questions };
                                  delete next[id];
                                  editQuestions(next);
                                }}
                              >
                                <Icon icon={faTrash} />
                              </button>
                            </div>
                            <label className="field-label">
                              INSTRUCTIONS
                              <textarea
                                className="instruction"
                                aria-label={`${id} instructions`}
                                value={q.instructions}
                                onChange={(e) =>
                                  editQuestions({
                                    ...questions,
                                    [id]: {
                                      ...q,
                                      instructions: e.target.value,
                                    },
                                  })
                                }
                              />
                            </label>
                            {q.type === "choice" && (
                              <div className="criteria">
                                {Object.entries(
                                  q.criteria as Record<string, string>,
                                ).map(([option, description]) => (
                                  <div className="criterion" key={option}>
                                    <code>{option}</code>
                                    <input
                                      aria-label={`${id} ${option} description`}
                                      value={description}
                                      onChange={(e) =>
                                        editQuestions({
                                          ...questions,
                                          [id]: {
                                            ...q,
                                            criteria: {
                                              ...(q.criteria as Record<
                                                string,
                                                string
                                              >),
                                              [option]: e.target.value,
                                            },
                                          },
                                        })
                                      }
                                    />
                                    <button
                                      className="icon-button"
                                      aria-label={`Remove ${id} option ${option}`}
                                      onClick={() => {
                                        const c = {
                                          ...(q.criteria as Record<
                                            string,
                                            string
                                          >),
                                        };
                                        delete c[option];
                                        editQuestions({
                                          ...questions,
                                          [id]: { ...q, criteria: c },
                                        });
                                      }}
                                    >
                                      <Icon icon={faTrash} />
                                    </button>
                                  </div>
                                ))}
                                <button
                                  className="text-button"
                                  onClick={() => {
                                    const option = prompt(
                                      "Option label (unique within this question)",
                                    );
                                    if (
                                      option &&
                                      !(option in (q.criteria || {}))
                                    )
                                      editQuestions({
                                        ...questions,
                                        [id]: {
                                          ...q,
                                          criteria: {
                                            ...(q.criteria as Record<
                                              string,
                                              string
                                            >),
                                            [option]: "Describe this option",
                                          },
                                        },
                                      });
                                  }}
                                >
                                  + Add option
                                </button>
                              </div>
                            )}
                            {q.type === "score" && (
                              <div className="score-levels">
                                {(q.criteria as string[]).map((text, i) => (
                                  <label key={i}>
                                    <code>{i}</code>
                                    <input
                                      aria-label={`${id} level ${i}`}
                                      value={text}
                                      onChange={(e) => {
                                        const c = [...(q.criteria as string[])];
                                        c[i] = e.target.value;
                                        editQuestions({
                                          ...questions,
                                          [id]: { ...q, criteria: c },
                                        });
                                      }}
                                    />
                                  </label>
                                ))}
                              </div>
                            )}
                            {q.type === "noul" && (
                              <p className="hint">
                                Returns the probability that the answer is yes.
                              </p>
                            )}
                          </div>
                        ))}
                        <button
                          className="add-question"
                          onClick={() => {
                            let id =
                              "question_" + (Object.keys(questions).length + 1);
                            while (id in questions) id += "_new";
                            editQuestions({
                              ...questions,
                              [id]: {
                                type: "choice",
                                instructions: "What decision should be made?",
                                criteria: {
                                  A: "First option",
                                  B: "Second option",
                                },
                              },
                            });
                          }}
                        >
                          <Icon icon={faPlus} /> Add a question
                        </button>
                      </div>
                    )}
                  </Panel>
                  <Panel title="03 / Run configuration">
                    <div className="run-config">
                      <label className="field-label">
                        CHECKPOINT
                        <ModelSelect
                          value={model}
                          onChange={setModel}
                          defaultOption
                        />
                      </label>
                      <details>
                        <summary>Token budgets & confidence</summary>
                        <div className="advanced">
                          <label>
                            Context tokens
                            <input
                              type="number"
                              placeholder="Model default"
                              value={context}
                              onChange={(e) => setContext(e.target.value)}
                              min="64"
                              max="8192"
                            />
                          </label>
                          <label>
                            Question head tokens
                            <input
                              type="number"
                              placeholder="Model default"
                              value={head}
                              onChange={(e) => setHead(e.target.value)}
                              min="16"
                              max="1024"
                            />
                          </label>
                          <label>
                            Minimum answer confidence
                            <input
                              type="number"
                              placeholder="Optional, 0–1"
                              value={threshold}
                              onChange={(e) => setThreshold(e.target.value)}
                              min="0"
                              max="1"
                              step="0.05"
                            />
                          </label>
                        </div>
                      </details>
                      <button
                        className="primary run-button"
                        disabled={!connected || busy}
                        onClick={() => void run()}
                      >
                        <Icon icon={faBolt} />
                        {busy ? "Running…" : "Run decision"}
                        <Icon icon={faArrowRight} />
                      </button>
                      <div className="request-actions">
                        <button
                          className="text-button"
                          onClick={() => {
                            try {
                              download("laya-request.json", payload());
                            } catch (e) {
                              setError((e as Error).message);
                            }
                          }}
                        >
                          <Icon icon={faDownload} /> Export request
                        </button>
                        <button
                          className="text-button"
                          onClick={() => {
                            try {
                              const body = JSON.stringify(payload());
                              void copy(
                                `import json, os, requests\npayload = json.loads(${JSON.stringify(body)})\nresponse = requests.post(${JSON.stringify(location.origin + "/api/v1/predict")}, headers={"Authorization": "Bearer " + os.environ["LAYA_API_KEY"]}, json=payload, timeout=180)\nresponse.raise_for_status()\nprint(response.json())`,
                              );
                            } catch (e) {
                              setError((e as Error).message);
                            }
                          }}
                        >
                          <Icon icon={faCopy} /> Copy Python
                        </button>
                      </div>
                    </div>
                  </Panel>
                </div>
                <div className="result-column">
                  <Panel
                    title="Decision output"
                    description="Typed answers with full probability distributions."
                    tools={
                      <button
                        className="text-button"
                        onClick={() => setRaw(!raw)}
                      >
                        <Icon icon={faCode} /> {raw ? "Visual" : "JSON"}
                      </button>
                    }
                  >
                    {!result ? (
                      <div className="empty-result">
                        <div className="empty-icon">
                          <Icon icon={faBolt} />
                        </div>
                        <h3>Your next decision starts here.</h3>
                        <p>
                          Run a request to see answers, probabilities and actual
                          GPU timing.
                        </p>
                        <div className="empty-flow">
                          <span>State</span>
                          <Icon icon={faArrowRight} />
                          <span>Questions</span>
                          <Icon icon={faArrowRight} />
                          <span>Decision</span>
                        </div>
                      </div>
                    ) : (
                      <>
                        <div className="result-meta">
                          <span className="tag cyan">
                            {names[result.routing.model]}
                          </span>
                          <span>{result.runtime.elapsed_ms.toFixed(0)} ms</span>
                          <code>{result.runtime.device}</code>
                        </div>
                        {result.runtime.warnings.map((w) => (
                          <div key={w} className="alert warning">
                            {w}
                          </div>
                        ))}
                        {raw ? (
                          <pre className="response-json">{pretty(result)}</pre>
                        ) : (
                          <div className="answers">
                            {Object.entries(result.answers).map(
                              ([id, answer]) => {
                                const criteria = resultQuestions[id]?.criteria;
                                const description = answer.type === "choice" && criteria && !Array.isArray(criteria)
                                  ? criteria[String(answer.choice)]
                                  : undefined;
                                const probabilities =
                                  (answer.probabilities as
                                    | Record<string, number>
                                    | undefined) ||
                                  (answer.type === "noul"
                                    ? {
                                        no: 1 - Number(answer.noul),
                                        yes: Number(answer.noul),
                                      }
                                    : {});
                                return (
                                  <article key={id} className="answer">
                                    <div className="answer-label">
                                      <span>{id}</span>
                                      <span className="tiny-tag">
                                        {String(answer.type)}
                                      </span>
                                    </div>
                                    <h3>
                                      {answer.type === "choice"
                                        ? String(answer.choice)
                                        : answer.type === "score"
                                          ? Number(answer.score).toFixed(2)
                                          : `${(Number(answer.noul) * 100).toFixed(1)}% yes`}
                                    </h3>
                                    {description && <p className="choice-description">{description}</p>}
                                    <div className="confidence">
                                      Answer confidence{" "}
                                      <strong>
                                        {(
                                          Number(answer.answer_confidence) * 100
                                        ).toFixed(1)}
                                        %
                                      </strong>
                                      {answer.low_confidence === true && (
                                        <span className="low-confidence">
                                          Below threshold
                                        </span>
                                      )}
                                    </div>
                                    {Object.entries(probabilities).map(
                                      ([label, p]) => (
                                        <div
                                          className="probability"
                                          key={label}
                                        >
                                          <div>
                                            <span>{label}</span>
                                            <code>{(p * 100).toFixed(1)}%</code>
                                          </div>
                                          <div className="bar-track">
                                            <div
                                              className="bar"
                                              style={{ width: `${p * 100}%` }}
                                            />
                                          </div>
                                        </div>
                                      ),
                                    )}
                                  </article>
                                );
                              },
                            )}
                          </div>
                        )}
                        <p className="routing-reason">
                          {result.routing.reason}
                        </p>
                        <div className="result-actions">
                          <button
                            className="text-button"
                            onClick={() => void copy(pretty(result))}
                          >
                            <Icon icon={faCopy} /> Copy JSON
                          </button>
                          <button
                            className="text-button"
                            onClick={() => download("laya-result.json", result)}
                          >
                            <Icon icon={faDownload} /> Export
                          </button>
                        </div>
                      </>
                    )}
                  </Panel>
                  <div className="reference-note">
                    <Icon icon={faCube} />
                    <div>
                      <strong>A decision model, not a chat model.</strong>
                      <p>
                        Laya returns typed answers. Validate accuracy and
                        calibration on your own data before relying on
                        probabilities.
                      </p>
                      <a href="/docs/agents.md" target="_blank">
                        Read the integration guide <Icon icon={faArrowRight} />
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
          {tab === "batch" && (
            <div className="batch-grid">
              <Panel
                title="Batch requests"
                description="A JSON array or one prediction request per JSONL line."
                tools={
                  <label className="file-button">
                    <Icon icon={faUpload} /> Import
                    <input
                      aria-label="Import batch"
                      type="file"
                      accept=".json,.jsonl,.txt"
                      onChange={(e) => void importBatch(e.target.files?.[0])}
                    />
                  </label>
                }
              >
                <textarea
                  className="code-editor batch-editor"
                  aria-label="Batch JSON"
                  value={batchText}
                  onChange={(e) => setBatchText(e.target.value)}
                  spellCheck={false}
                />
                <div className="batch-controls">
                  <label>
                    States per forward
                    <select
                      aria-label="Batch size"
                      value={microbatch}
                      onChange={(e) => setMicrobatch(Number(e.target.value))}
                    >
                      <option value="1">1 · lower memory</option>
                      <option value="2">2 · default</option>
                    </select>
                  </label>
                  <button
                    className="primary"
                    disabled={!connected || busy}
                    onClick={() => void runBatch()}
                  >
                    <Icon icon={faBolt} /> Run batch
                  </button>
                </div>
                <p className="hint padded">
                  Up to 32 requests. Requests sharing a checkpoint are grouped
                  to reduce reloads. Results retain input order.
                </p>
              </Panel>
              <Panel
                title="Ordered results"
                tools={
                  batchResult && (
                    <button
                      className="text-button"
                      onClick={() =>
                        download("laya-batch-results.json", batchResult)
                      }
                    >
                      <Icon icon={faDownload} /> Export
                    </button>
                  )
                }
              >
                {batchResult ? (
                  <>
                    <div className="result-meta">
                      <span>{batchResult.results.length} results</span>
                      <span>
                        {batchResult.runtime.elapsed_ms.toFixed(0)} ms total
                      </span>
                    </div>
                    {batchResult.results.map((r, i) => (
                      <details className="batch-row" key={i}>
                        <summary>
                          <span className="number">
                            {String(i + 1).padStart(2, "0")}
                          </span>
                          {names[r.routing.model]}
                          <span>{r.runtime.device}</span>
                        </summary>
                        <pre>{pretty(r)}</pre>
                      </details>
                    ))}
                  </>
                ) : (
                  <div className="empty-result">
                    <Icon icon={faLayerGroup} />
                    <h3>A clear view of every result.</h3>
                    <p>Import a batch or try the three-language example.</p>
                  </div>
                )}
              </Panel>
            </div>
          )}
          {tab === "models" && (
            <>
              <div className="section-toolbar">
                <div>
                  <h2>Choose your default</h2>
                  <p>
                    Applies to every request that does not explicitly choose a
                    model.
                  </p>
                </div>
                <button
                  className="secondary"
                  disabled={!connected || busy}
                  onClick={() => void defaultModel("auto")}
                >
                  <Icon icon={faRotate} /> Use automatic routing
                </button>
              </div>
              <div className="model-grid">
                {models.map((m) => (
                  <SpotlightCard
                    key={m.id}
                    className={`model-card ${status?.default_model === m.id ? "chosen" : ""}`}
                    spotlightColor="rgba(126, 92, 255, 0.15)"
                  >
                    <div className="model-icon">
                      <Icon
                        icon={
                          m.id === "multilingual"
                            ? faLayerGroup
                            : m.id === "english"
                              ? faCube
                              : faBolt
                        }
                      />
                    </div>
                    <span className="tiny-tag">
                      {m.resident
                        ? "RESIDENT ON GPU"
                        : m.downloaded
                          ? "DOWNLOADED"
                          : "NOT DOWNLOADED"}
                    </span>
                    <h2>{m.title}</h2>
                    <p>{m.description}</p>
                    <div className="model-spec">
                      <span>Default context</span>
                      <strong>{m.context.toLocaleString()} tokens</strong>
                    </div>
                    <div className="model-spec">
                      <span>Question budget</span>
                      <strong>{m.head} tokens</strong>
                    </div>
                    <button className="secondary" onClick={() => {setGuideModel(m.id); setTab("model-guide"); history.replaceState(null, "", `/model-guide#${m.id}`);}}>
                      <Icon icon={faBookOpen}/> Learn about {m.title}
                    </button>
                    <button
                      className={
                        status?.default_model === m.id ? "secondary" : "primary"
                      }
                      disabled={!connected || busy}
                      onClick={() => void defaultModel(m.id)}
                    >
                      {status?.default_model === m.id ? (
                        <>
                          <Icon icon={faCheck} /> Saved default
                        </>
                      ) : (
                        <>
                          Use as default <Icon icon={faArrowRight} />
                        </>
                      )}
                    </button>
                  </SpotlightCard>
                ))}
              </div>
              <div className="reference-note">
                <Icon icon={faRotate} />
                <div>
                  <strong>Switching checkpoints adds loading time.</strong>
                  <p>
                    The current checkpoint is unloaded before the next is
                    loaded. An explicit prediction model never changes your
                    saved default.
                  </p>
                </div>
              </div>
              <Panel
                title="Runtime status"
                description="The actual device, memory, package versions and recent error."
              >
                <pre className="status-json">
                  {status
                    ? pretty(status)
                    : "Connect your API key to inspect the runtime."}
                </pre>
              </Panel>
            </>
          )}
          {tab === "benchmark" && <BenchmarkView connected={connected} load={() => api("/api/v1/benchmark")} useExample={(p, title) => {
            setStateMode(typeof p.state === "string" ? "text" : "json");
            setStateText(typeof p.state === "string" ? p.state : pretty(p.state));
            setQuestionText(pretty(p.questions)); setModel(""); setContext("512"); setHead("192"); setThreshold("0.8");
            setResult(null); setTab("playground"); setNotice(title); setError("");
          }} />}
          {tab === "model-guide" && <ModelGuide selected={guideModel} select={(id) => {setGuideModel(id); history.replaceState(null, "", `/model-guide#${id}`);}} useExample={(p, title) => {
            setStateMode(typeof p.state === "string" ? "text" : "json");
            setStateText(typeof p.state === "string" ? p.state : pretty(p.state));
            setQuestionText(pretty(p.questions)); setModel(p.model || "");
            setContext(String(p.max_len || "")); setHead(String(p.head_max_len || "")); setThreshold(String(p.min_confidence ?? ""));
            setResult(null); setTab("playground"); setNotice(title); setError("");
            history.replaceState(null, "", "/");
          }}/>}
          {tab === "guide" && (
            <div className="guide-grid">
              <Panel
                title="HTTP API"
                description="Use your own app’s HTTP client."
              >
                <div className="guide-body">
                  <span className="tiny-tag">BASE URL</span>
                  <pre>{location.origin + "/api/v1"}</pre>
                  <p>
                    Send <code>Authorization: Bearer &lt;LAYA_API_KEY&gt;</code>
                    . Start with a state and a named set of typed questions.
                  </p>
                  <pre>{pretty(presets["Sentiment choice"])}</pre>
                  <div className="guide-links">
                    <a href="/docs" target="_blank">
                      Interactive API docs <Icon icon={faArrowRight} />
                    </a>
                    <a href="/openapi.json" target="_blank">
                      OpenAPI schema <Icon icon={faArrowRight} />
                    </a>
                  </div>
                </div>
              </Panel>
              <Panel
                title="For AI agents"
                description="Fetch Markdown or connect through MCP."
              >
                <div className="guide-body">
                  <span className="tiny-tag">MCP · STREAMABLE HTTP</span>
                  <pre>{location.origin + "/mcp/"}</pre>
                  <p>
                    The MCP endpoint uses the same bearer key and GPU worker as
                    the HTTP API.
                  </p>
                  <div className="tool-list">
                    {[
                      "laya_predict",
                      "laya_predict_batch",
                      "laya_models",
                      "laya_model_info",
                      "laya_status",
                      "laya_set_default_model",
                    ].map((t) => (
                      <code key={t}>
                        <Icon icon={faTerminal} /> {t}
                      </code>
                    ))}
                  </div>
                  <div className="guide-links">
                    <a href="/llms.txt" target="_blank">
                      Agent discovery / llms.txt <Icon icon={faArrowRight} />
                    </a>
                    <a href="/docs/models.md" target="_blank">Model capability guide <Icon icon={faArrowRight}/></a>
                    <a href="/models.json" target="_blank">Model metadata JSON <Icon icon={faArrowRight}/></a>
                    <a href="/docs/agents.md" target="_blank">
                      Integration guide <Icon icon={faArrowRight} />
                    </a>
                    <a href="/docs/architecture.md" target="_blank">
                      How it works <Icon icon={faArrowRight} />
                    </a>
                  </div>
                  <p className="hint">
                    Backend and desktop clients can connect on the local
                    network. Third-party browser origins are disabled.
                  </p>
                </div>
              </Panel>
            </div>
          )}
          <footer className="page-footer">
            <span>
              Built for local decisions.{" "}
              <span className="muted">Powered by Laya · Python · PyTorch</span>
            </span>
            <a href="/credits.txt" target="_blank">
              React Bits & Font Awesome Free
            </a>
          </footer>
          {!reduced && !working && (
            <FadeContent duration={0.4} delay={0} className="bottom-accent">
              <span />
            </FadeContent>
          )}
        </div>
      </main>
    </div>
  );
}
