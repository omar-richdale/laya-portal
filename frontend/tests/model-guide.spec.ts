// Public learning and local budget exploration must not execute inference or settings changes.
import {test, expect} from "@playwright/test";

test("learn every checkpoint without a key and load an explicit example", async ({page}) => {
  const mutations: string[] = [];
  page.on("request", r => {if (r.method() !== "GET") mutations.push(r.url());});
  await page.setViewportSize({width:1440, height:1100});
  await page.goto("/model-guide#typed-decisions");
  await expect(page.getByRole("heading", {name:"Typed decisions: when to use it"})).toBeVisible();
  await expect(page.getByLabel("Total token budget")).toHaveValue("1024");
  await expect(page.getByLabel("Question token budget")).toHaveValue("256");
  await page.getByRole("button", {name:/^English 421M/}).click();
  await expect(page.getByLabel("Total token budget")).toHaveValue("512");
  await page.getByLabel("Total token budget").fill("8192");
  await expect(page.getByRole("alert")).toContainText("within this model's limits");
  await page.getByRole("button", {name:/^Multilingual 322M/}).click();
  await page.getByLabel("Total token budget").fill("8192");
  await page.getByLabel("Question token budget").fill("512");
  await expect(page.locator(".budget-legend")).toContainText(/7[.,]680/);
  await expect(page.locator(".learning-table")).toContainText("170 / 233");
  await page.getByText("Fetch from an AI agent", {exact:true}).click();
  await expect(page.locator(".model-learning")).toContainText("laya://model-guide");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({path:"test-results/model-guide-desktop.png"});
  await page.locator(".learning-columns").first().screenshot({path:"test-results/model-guide-budgets.png"});
  const typed = page.getByRole("button", {name:/^Typed decisions 421M/});
  await typed.focus();
  await page.keyboard.press("Enter");
  await expect(typed).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", {name:"Try Typed decisions example", exact:true}).click();
  await expect(page.getByLabel("Request model")).toHaveValue("typed-decisions");
  await expect(page.getByLabel("Context tokens")).toHaveValue("1024");
  await expect(page.getByLabel("Question head tokens")).toHaveValue("256");
  expect(mutations).toEqual([]);
});

test("model guide remains readable offline on a narrow reduced-motion screen", async ({page}) => {
  await page.setViewportSize({width:390, height:844});
  await page.emulateMedia({reducedMotion:"reduce"});
  await page.route(/https:\/\//, route => route.abort());
  await page.goto("/model-guide#multilingual");
  await expect(page.getByRole("heading", {name:"Multilingual: when to use it"})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({path:"test-results/model-guide-mobile-top.png"});
  await page.screenshot({path:"test-results/model-guide-mobile.png", fullPage:true});
  await page.locator(".learning-panel").first().screenshot({path:"test-results/model-guide-mobile-budget.png"});
  const response = await page.request.get("/models.json");
  expect(response.ok()).toBe(true);
  expect((await response.json()).models).toHaveLength(3);
});
