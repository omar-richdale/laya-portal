// Saved comparisons and live replays use the same scoring and timing rules.
import type { Prediction, Result } from "./types";

export const checkpoints = ["english", "multilingual", "typed-decisions"] as const;
export type Checkpoint = typeof checkpoints[number];
export const checkpointNames: Record<Checkpoint, string> = { english: "English", multilingual: "Multilingual", "typed-decisions": "Typed decisions" };
export type SuiteCase = { id: string; prompt: string; expected: string; prediction: Prediction };
export type SuiteTask = { id: string; title: string; description: string; policy: string; criteria: Record<string, string>; cases: SuiteCase[] };
export type Observation = {
  model: Checkpoint; task: string; case_id: string; choice: string; confidence: number;
  service_ms: number; http_ms: number; device: string; valid: boolean;
  probabilities: Record<string, number>; warnings: string[]; usage: Record<string, unknown>;
};
export type Replay = {
  created_at: string; fixture_sha256: string; request_sha256: string; models: Checkpoint[];
  warmups: { model: Checkpoint; service_ms: number; load_ms: number }[];
  records: Observation[]; environment?: { gpu: string; revision: string };
  status?: "running" | "completed" | "stopped" | "failed";
};
export type Catalog = { version: number; fixture_sha256: string; request_sha256: string; tasks: SuiteTask[]; baseline: Replay };
export type Api = <T>(path: string, body?: unknown, method?: string) => Promise<T>;

export function percentile(values: number[], p: number): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const index = (sorted.length - 1) * p;
  const low = Math.floor(index), high = Math.ceil(index);
  return sorted[low] + (sorted[high] - sorted[low]) * (index - low);
}

export function observed(result: Result, model: Checkpoint, task: SuiteTask, item: SuiteCase, httpMs: number): Observation {
  const answer = result.answers.decision;
  const usage = result.usage || {};
  const choice = String(answer?.choice ?? "");
  // A matching label on a truncated or misrouted request is not a successful replay.
  const valid = result.routing.model === model && Boolean(task.criteria[choice]) &&
    !usage.truncated && !(Number(usage.state_tokens_dropped) > 0) &&
    !(Array.isArray(usage.truncated_questions) && usage.truncated_questions.length > 0);
  return { model, task: task.id, case_id: item.id, choice, confidence: Number(answer?.answer_confidence || 0),
    service_ms: result.runtime.elapsed_ms, http_ms: httpMs, device: result.runtime.device, valid,
    probabilities: (answer?.probabilities || {}) as Record<string, number>,
    warnings: result.runtime.warnings || [], usage };
}

export function stats(rows: Observation[], tasks: SuiteTask[]) {
  const references = new Map(tasks.flatMap(t => t.cases.map(c => [c.id, c.expected] as const)));
  const matches = rows.filter(r => r.valid && references.get(r.case_id) === r.choice).length;
  const confident = rows.filter(r => r.confidence >= 0.8);
  return {
    count: rows.length, matches, accuracy: rows.length ? matches / rows.length : null,
    median: percentile(rows.map(r => r.service_ms), 0.5), p95: percentile(rows.map(r => r.service_ms), 0.95),
    httpMedian: percentile(rows.map(r => r.http_ms), 0.5),
    confident: confident.length,
    confidentErrors: confident.filter(r => !r.valid || references.get(r.case_id) !== r.choice).length,
    incomplete: rows.filter(r => !r.valid).length,
    unsafeAllows: rows.filter(r => references.get(r.case_id) === "block" && r.choice === "allow").length,
    benignBlocks: rows.filter(r => references.get(r.case_id) === "allow" && r.choice === "block").length,
    referrals: rows.filter(r => r.choice === "review").length,
  };
}

export function exportJson(name: string, value: unknown) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = name; anchor.click();
  URL.revokeObjectURL(url);
}
