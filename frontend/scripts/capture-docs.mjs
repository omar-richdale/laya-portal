// Capture the actual local portal; credentials and browser storage never leave this process.
// Only predictions are submitted. Saved defaults, source issues and other services stay untouched.
import {chromium, expect} from '@playwright/test';
import {readFileSync, mkdirSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root = new URL('../../', import.meta.url);
const env = readFileSync(new URL('.env', root), 'utf8');
const value = name => env.match(new RegExp(`^${name}=(.+)$`, 'm'))?.[1].trim().replace(/^['"]|['"]$/g, '');
const key = value('LAYA_API_KEY');
if (!key) throw new Error('Configure the project .env before capturing the portal.');
const baseURL = `http://127.0.0.1:${value('LAYA_PORT') || '8000'}`;
const output = new URL('docs/screenshots/', root);
mkdirSync(output, {recursive:true});
const browser = await chromium.launch({channel:'msedge', headless:true});
const context = await browser.newContext({baseURL, viewport:{width:1600, height:1200}, locale:'en-US', reducedMotion:'reduce'});
const page = await context.newPage();
const errors = [];
page.on('pageerror', e => errors.push(e.message));
const screenshots = [];
async function snapshot(name, caption, locator) {
  await page.evaluate(() => document.fonts.ready);
  const path = fileURLToPath(new URL(name, output));
  if (locator) await locator.screenshot({path, animations:'disabled'});
  else await page.screenshot({path, animations:'disabled'});
  screenshots.push({file:name, caption, sha256:createHash('sha256').update(readFileSync(path)).digest('hex')});
  console.log(`Captured ${name}`);
}
async function status() {
  const response = await context.request.get('/api/v1/status', {headers:{Authorization:`Bearer ${key}`}});
  if (!response.ok()) throw new Error(`Local status request returned ${response.status()}.`);
  return response.json();
}
async function visit(name) {
  await page.getByRole('button', {name, exact:true}).click();
  await page.evaluate(() => scrollTo(0, 0));
}
try {
  const before = await status();
  await page.goto('/');
  await page.getByLabel('API key', {exact:true}).fill(key);
  await page.getByRole('button', {name:'Connect', exact:true}).click();
  await expect(page.getByText('Authenticated for this tab')).toBeVisible();
  await page.getByLabel('Request model').selectOption('english');
  await page.getByRole('button', {name:'Run decision', exact:true}).click();
  await expect(page.locator('.answers .answer')).toHaveCount(3, {timeout:180000});
  await expect(page.locator('.result-meta')).toContainText('cuda:0');
  await expect(page.locator('.activity')).toHaveCount(0, {timeout:30000});
  const prediction = await page.locator('.result-meta').innerText();
  await page.evaluate(() => scrollTo(0, 480));
  await snapshot('playground.png', 'Live English support-ticket decision with choice, score and yes-probability outputs on CUDA.');

  await visit('Models & GPU');
  await expect(page.locator('.model-card')).toHaveCount(3);
  await page.locator('.model-grid').scrollIntoViewIfNeeded();
  await snapshot('models-status.png', 'All three downloaded checkpoints, saved default and live GPU status.');

  await visit('Model guide');
  await page.getByRole('button', {name:/^English 421M/}).click();
  await expect(page.getByRole('heading', {name:'English: when to use it'})).toBeVisible();
  await page.evaluate(() => scrollTo(0, 490));
  await snapshot('model-guide.png', 'Offline checkpoint guide with language, use cases, local evidence and token budgets.');

  await visit('Real benchmark');
  await expect(page.getByRole('heading', {name:'Your issues, your GPU'})).toBeVisible();
  await page.evaluate(() => scrollTo(0, 465));
  await snapshot('real-benchmark.png', 'Frozen October 1 benchmark: three models, 247 reference cases, measured timings and understandable replay examples.');

  await visit('Batch testing');
  const questions = {team:{type:'choice', instructions:'Which team should handle this request?', criteria:{billing:'duplicate charges and refunds', technical:'broken apps or connectivity'}}};
  const requests = [{model:'english', state:'I was charged twice. Please refund the duplicate payment.', questions}, {model:'multilingual', state:'J’ai été facturé deux fois. Merci de rembourser le paiement en double.', questions}, {model:'multilingual', state:'تم خصم المبلغ مرتين. أرجو إعادة المبلغ الزائد.', questions}];
  await page.getByLabel('Batch JSON').fill(JSON.stringify(requests, null, 2));
  await page.getByRole('button', {name:'Run batch', exact:true}).click();
  await expect(page.locator('.batch-row')).toHaveCount(3, {timeout:180000});
  for (const row of await page.locator('.batch-row').all()) await expect(row).toContainText('cuda:0');
  await page.locator('.batch-row').first().locator('summary').click();
  await page.getByLabel('Batch JSON').evaluate(element => { element.scrollTop = 0; });
  await page.evaluate(() => scrollTo(0, 635));
  await snapshot('batch.png', 'Live ordered English, French and Arabic batch using explicit checkpoint overrides.');

  await visit('Integration');
  await page.evaluate(() => scrollTo(0, 465));
  await snapshot('integration.png', 'REST and MCP integration discovery with placeholder credentials and local documentation.');

  await page.setViewportSize({width:390, height:844});
  await page.goto('/model-guide#multilingual');
  await expect(page.getByRole('heading', {name:'Multilingual: when to use it'})).toBeVisible();
  if (!(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth))) throw new Error('Mobile page overflows horizontally.');
  await snapshot('mobile-token-budget.png', 'Multilingual token-budget guide on a 390px reduced-motion viewport.', page.locator('.learning-panel').first());
  const after = await status();
  if (before.default_model !== after.default_model) throw new Error('Screenshot capture changed the saved default.');
  if (errors.length) throw new Error(`Portal raised ${errors.length} browser errors.`);
  const report = {captured_at:new Date().toISOString(), source:'Actual locally running service; no API fixtures or mocked predictions', viewport:{desktop:[1600,1200],mobile:[390,844]}, motion:'reduced; screenshot animations disabled', credentials:'Never written to screenshots, manifest or traces; no browser profile persisted', saved_default_unchanged:after.default_model, live_prediction:prediction, device:after.device, revision:after.revision, screenshots};
  writeFileSync(new URL('manifest.json', output), JSON.stringify(report, null, 2) + '\n');
} finally {
  await context.close();
  await browser.close();
}
