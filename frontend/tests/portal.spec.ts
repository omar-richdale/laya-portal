// Browser checks cover editing, authentication, output rendering, batch order and accessibility.
import { test, expect } from "@playwright/test";
const runtime = {
  ready: true,
  phase: "idle",
  device: "cuda:0",
  resident_model: "english",
  default_model: "auto",
  outstanding_jobs: 0,
  max_jobs: 8,
  load_ms: 3000,
  versions: {
    laya: "0.3.22",
    torch: "2.10.0+cu128",
    transformers: "4.57.6",
    mcp: "2.2.0",
  },
  revision: "test",
  last_error: null,
  gpu: {
    name: "NVIDIA GeForce RTX 4050 Laptop GPU",
    free_bytes: 4 * 1024 ** 3,
    total_bytes: 6 * 1024 ** 3,
    allocated_bytes: 2 * 1024 ** 3,
    peak_allocated_bytes: 3 * 1024 ** 3,
  },
};
const result = {
  model: "laya-rl-agent",
  answers: {
    department: {
      type: "choice",
      choice: "billing",
      probabilities: { billing: 0.91, technical: 0.05, other: 0.04 },
      answer_confidence: 0.86,
    },
  },
  routing: { model: "english", reason: "English input" },
  usage: { input_tokens: 92, output_tokens: 0 },
  runtime: {
    device: "cuda:0",
    revision: "test",
    elapsed_ms: 64,
    load_ms: 3000,
    warnings: [],
  },
};
const models = ["english", "multilingual", "typed-decisions"].map((id) => ({
  id,
  title:
    id === "english"
      ? "English"
      : id === "multilingual"
        ? "Multilingual"
        : "Typed decisions",
  description: "Reference checkpoint",
  context: id === "english" ? 512 : 1024,
  head: 256,
  downloaded: true,
  resident: id === "english",
  revision: "test",
}));

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = runtime;
    if (path.endsWith("/models") || path.endsWith("/settings/model"))
      data = { models, default_model: "auto", resident_model: "english" };
    if (path.endsWith("/predict")) data = result;
    if (path.endsWith("/predict/batch"))
      data = {
        results: [
          result,
          {
            ...result,
            routing: { model: "multilingual", reason: "French input" },
          },
        ],
        runtime: { elapsed_ms: 120 },
      };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(data),
    });
  });
});

async function connect(page: import("@playwright/test").Page) {
  await page.goto("/");
  await page
    .getByRole("textbox", { name: "API key" })
    .fill("browser-test-key-not-a-secret");
  await page.getByRole("button", { name: "Connect", exact: true }).click();
  await expect(page.getByText("Authenticated for this tab")).toBeVisible();
}

test("connect, edit questions, run, inspect raw output and export", async ({
  page,
}) => {
  await connect(page);
  await page
    .getByRole("textbox", { name: "State input" })
    .fill("Please refund the duplicate payment.");
  await page.getByRole("button", { name: "Add a question" }).click();
  await expect(page.getByLabel("question_4 instructions")).toBeVisible();
  await page
    .getByRole("button", { name: "Remove question_4", exact: true })
    .click();
  await page.getByRole("button", { name: "Run decision" }).click();
  await expect(
    page.getByRole("heading", { name: "billing", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("91.0%")).toBeVisible();
  await page.getByRole("button", { name: "JSON", exact: true }).last().click();
  await expect(page.locator(".response-json")).toContainText("cuda:0");
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export request" }).click();
  expect((await downloaded).suggestedFilename()).toBe("laya-request.json");
  await page.screenshot({
    path: "test-results/playground.png",
    fullPage: true,
  });
});

test("batch, model defaults and integration", async ({ page }) => {
  await connect(page);
  await page
    .getByRole("button", { name: "Batch testing", exact: true })
    .click();
  await page.getByRole("button", { name: "Run batch" }).click();
  await expect(page.getByText("2 results", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Models & GPU", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Three checkpoints/ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Use as default" }).nth(1).click();
  await expect(
    page.getByText("Multilingual is now the saved service default."),
  ).toBeVisible();
  await page.getByRole("button", { name: "Integration", exact: true }).click();
  await expect(
    page.getByText("laya_predict", { exact: false }).first(),
  ).toBeVisible();
});

test("mobile reduced-motion layout, offline assets and escaped content", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  const external: string[] = [];
  page.on("request", (req) => {
    if (
      !req.url().startsWith("http://127.0.0.1:8000") &&
      !req.url().startsWith("data:")
    )
      external.push(req.url());
  });
  await connect(page);
  await expect(page.locator(".bottom-accent")).toHaveCount(0);
  await page
    .getByLabel("State input")
    .fill("<script>window.injected=true</script>");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(external).toEqual([]);
  expect(await page.evaluate(() => "injected" in window)).toBe(false);
  await page.screenshot({ path: "test-results/mobile.png", fullPage: true });
});
