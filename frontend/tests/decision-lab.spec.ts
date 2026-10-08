// Browser fixtures exercise replay controls and partial runs without spending GPU time.
import { test, expect } from "@playwright/test";
import type { Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import type { Catalog } from "../src/labMetrics";

const fixtures = JSON.parse(readFileSync(new URL("../../docs/benchmark/everyday-fixtures.json", import.meta.url), "utf8"));
const baseline = JSON.parse(readFileSync(new URL("../../docs/benchmark/everyday-baseline.json", import.meta.url), "utf8"));
const titles: Record<string, string> = { model_routing: "Model routing", support_routing: "Support routing", sentiment: "Sentiment", chat_moderation: "Chat moderation", image_moderation: "Image prompts", video_moderation: "Video prompts" };
const catalog: Catalog = { version: 1, fixture_sha256: baseline.fixture_sha256, request_sha256: baseline.request_sha256, baseline,
  tasks: Object.entries(titles).map(([id, title]) => {
    const t = fixtures[id];
    return { id, title, description: "Replay this fixed study.", policy: t.policy, criteria: t.criteria,
      cases: t.cases.map(([expected, prompt]: [string, string], i: number) => ({ id: `${id}-${String(i + 1).padStart(2, "0")}`, prompt, expected,
        prediction: { state: { policy: t.policy, request: prompt }, questions: { decision: { type: "choice", instructions: "Classify", criteria: t.criteria } }, min_confidence: .8 } })) };
  }) };

async function setup(page: Page, options: { delay?: number; failAt?: number } = {}) {
  const calls: Record<string, unknown>[] = [];
  await page.route("**/api/v1/**", async route => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    if (path.endsWith("/status")) data = { ready: true, phase: "idle", device: "cuda:0", default_model: "english", resident_model: "english", outstanding_jobs: 0, max_jobs: 8, load_ms: 2000, versions: {}, gpu: { name: "RTX 4050 Laptop GPU", free_bytes: 3.5 * 1024 ** 3 } };
    if (path.endsWith("/models")) data = { models: [], default_model: "english", resident_model: "english" };
    if (path.endsWith("/decision-suite")) data = catalog;
    if (path.endsWith("/predict")) {
      const request = route.request().postDataJSON();
      calls.push(request);
      if (options.delay) await new Promise(resolve => setTimeout(resolve, options.delay));
      if (calls.length === options.failAt) {
        await route.fulfill({ status: 503, json: { error: { message: "GPU temporarily unavailable" } } });
        return;
      }
      const item = catalog.tasks.flatMap(t => t.cases).find(c => c.prompt === request.state.request)!;
      const choice = item.id === "sentiment-01" ? "neutral" : item.expected;
      data = { answers: { decision: { choice, answer_confidence: .9, probabilities: { [choice]: .9 } } },
        routing: { model: request.model, reason: "fixture" }, usage: { truncated: false },
        runtime: { device: "cuda:0", elapsed_ms: calls.length === 1 ? 2200 : 60, load_ms: 2000, warnings: [], revision: "fixture" } };
    }
    await route.fulfill({ status: 200, json: data });
  });
  await page.goto("/batch#decision-lab");
  await page.getByRole("textbox", { name: "API key" }).fill("browser-test-key-not-a-secret");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Know what it’s good at." })).toBeVisible();
  return calls;
}

async function sentimentOnly(page: Page) {
  await page.getByRole("checkbox", { name: "Multilingual", exact: true }).uncheck();
  await page.getByRole("checkbox", { name: "Typed decisions", exact: true }).uncheck();
  for (const title of Object.values(titles).filter(t => t !== "Sentiment")) await page.getByRole("checkbox", { name: `Include ${title}`, exact: true }).uncheck();
}

test("saved comparison, confusion, exports and responsive layout", async ({ page }) => {
  const calls = await setup(page);
  await expect(page.locator(".lab-kpis")).toContainText("390");
  await expect(page.getByRole("button", { name: "Inspect Sentiment, Typed decisions", exact: true })).toContainText("100.0%");
  await page.getByRole("button", { name: "Inspect Image prompts, Multilingual", exact: true }).click();
  await expect(page.getByLabel("Inspect suite")).toHaveValue("image_moderation");
  await page.getByText("Policy, labels and confusion table", { exact: true }).click();
  await expect(page.locator(".lab-confusion")).toContainText("allow");
  await page.getByLabel("Filter decisions").selectOption("misses");
  await expect(page.locator(".lab-case-table tbody tr")).toHaveCount(16);
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export suite requests" }).click();
  const file = await download;
  const requests = JSON.parse(readFileSync((await file.path())!, "utf8"));
  expect(requests).toHaveLength(24);
  expect(requests[0].model).toBe("multilingual");
  expect(requests[0].expected).toBeUndefined();
  expect(calls).toHaveLength(0);
  await page.setViewportSize({ width: 1440, height: 1100 });
  await page.locator(".lab-comparison").screenshot({ path: "test-results/decision-lab-comparison.png" });
  await page.locator(".decision-lab").screenshot({ path: "test-results/decision-lab-desktop.png" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.locator(".decision-lab").screenshot({ path: "test-results/decision-lab-mobile.png" });
});

test("selected replay excludes warm-up and preserves original references", async ({ page }) => {
  const calls = await setup(page);
  await sentimentOnly(page);
  await page.getByRole("button", { name: "Run selected tests" }).click();
  await expect(page.getByText("Replay complete", { exact: true })).toBeVisible();
  expect(calls).toHaveLength(19);
  expect(calls.every(c => c.model === "english" && !("expected" in c))).toBe(true);
  await expect(page.locator(".lab-kpis")).toContainText("94.4%");
  await expect(page.locator(".lab-kpis")).toContainText("60.0 ms");
  await expect(page.locator(".lab-detail-metrics")).toContainText("17/18");
  await page.getByLabel("Filter decisions").selectOption("misses");
  await expect(page.locator(".lab-case-table tbody tr")).toHaveCount(1);
  await page.getByRole("button", { name: "Saved comparison", exact: true }).click();
  await expect(page.locator(".lab-kpis")).toContainText("390");
});

test("stop retains partial results even when switching batch sections", async ({ page }) => {
  const calls = await setup(page, { delay: 180 });
  await sentimentOnly(page);
  await page.getByRole("button", { name: "Run selected tests" }).click();
  await expect.poll(() => calls.length).toBeGreaterThan(2);
  await page.getByRole("button", { name: "Custom batch", exact: true }).click();
  await page.getByRole("button", { name: /Decision lab/ }).click();
  await page.getByRole("button", { name: "Stop after current request", exact: true }).click();
  await expect(page.getByText("Stopped · completed results retained", { exact: true })).toBeVisible();
  expect(calls.length).toBeLessThan(19);
  await expect(page.locator(".lab-comparison .lab-heading")).toContainText("stopped");
  await expect(page.getByRole("button", { name: "Run selected tests" })).toBeEnabled();
});

test("failure retains completed decisions and marks the run interrupted", async ({ page }) => {
  await setup(page, { failAt: 4 });
  await sentimentOnly(page);
  await page.getByRole("button", { name: "Run selected tests" }).click();
  await expect(page.locator(".lab-error")).toContainText("GPU temporarily unavailable");
  await expect(page.getByText("Replay interrupted · completed results retained", { exact: true })).toBeVisible();
  await expect(page.locator(".lab-detail-metrics")).toContainText("1/2");
  await expect(page.locator(".lab-comparison .lab-heading")).toContainText("failed");
});
