// An incomplete or partial replay must not inflate accuracy or confidence coverage.
import { test, expect } from "@playwright/test";
import { observed, percentile, stats } from "../src/labMetrics";
import type { Observation, SuiteTask } from "../src/labMetrics";
import type { Result } from "../src/types";

const task: SuiteTask = { id: "test", title: "Test", description: "", policy: "", criteria: { allow: "allow", block: "block" }, cases: [
  { id: "test-1", prompt: "safe", expected: "allow", prediction: { state: "safe", questions: {} } },
  { id: "test-2", prompt: "unsafe", expected: "block", prediction: { state: "unsafe", questions: {} } },
] };
const row: Observation = { model: "english", task: "test", case_id: "test-1", choice: "allow", confidence: .9,
  service_ms: 60, http_ms: 65, device: "cuda:0", valid: true, warnings: [], probabilities: {}, usage: {} };

test("metrics preserve partial denominators, error direction and threshold coverage", () => {
  const result = stats([row, { ...row, case_id: "test-2", service_ms: 80, http_ms: 90 }], [task]);
  expect(result.accuracy).toBe(.5);
  expect(result.unsafeAllows).toBe(1);
  expect(result.benignBlocks).toBe(0);
  expect(result.confidentErrors).toBe(1);
  expect(result.confident).toBe(2);
  expect(result.median).toBe(70);
  expect(result.p95).toBe(79);
  expect(stats([row], [task]).accuracy).toBe(1);
  expect(stats([], [task]).accuracy).toBeNull();
  expect(percentile([], .95)).toBeNull();
});

test("truncated and misrouted answers cannot count as reference matches", () => {
  const result: Result = { answers: { decision: { choice: "allow", answer_confidence: .99 } },
    routing: { model: "english", reason: "test" }, usage: { truncated: true },
    runtime: { device: "cuda:0", elapsed_ms: 60, load_ms: 3000, revision: "test", warnings: [] } };
  const invalid = observed(result, "english", task, task.cases[0], 65);
  expect(invalid.valid).toBe(false);
  expect(stats([invalid], [task]).matches).toBe(0);
  expect(stats([invalid], [task]).confidentErrors).toBe(1);
  expect(observed({ ...result, usage: {}, routing: { model: "multilingual", reason: "wrong" } }, "english", task, task.cases[0], 65).valid).toBe(false);
});
