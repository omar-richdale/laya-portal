// Opt in to a real GPU browser request; credentials are never saved in screenshots or traces.
import {test,expect} from '@playwright/test';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';

test('real CUDA service through the production portal',async({page})=>{
  test.skip(process.env.LAYA_LIVE_TEST!=='1','Set LAYA_LIVE_TEST=1 to exercise the actual GPU service.');
  test.setTimeout(180000);
  const env=readFileSync(new URL('../../.env',import.meta.url),'utf8');
  const key=env.match(/^LAYA_API_KEY=(.+)$/m)![1].trim();
  const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.setViewportSize({width:1440,height:1100});
  await page.goto('/');
  await page.getByLabel('API key',{exact:true}).fill(key);
  await page.getByRole('button',{name:'Connect',exact:true}).click();
  await expect(page.getByText('Authenticated for this tab')).toBeVisible();
  await page.getByRole('button',{name:'Run decision'}).click();
  await expect(page.locator('.answers .answer')).toHaveCount(3,{timeout:150000});
  await expect(page.locator('.result-meta')).toContainText('cuda:0');
  await expect(page.locator('.activity')).toHaveCount(0,{timeout:30000});
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:'test-results/live-portal.png',fullPage:true});
  expect(errors).toEqual([]);
  // Swagger must render using local assets when external requests are unavailable.
  await page.route(/https:\/\/(?!127\.0\.0\.1)/,route=>route.abort());
  await page.goto('/docs');
  await expect(page.getByRole('heading',{name:/Laya Local/}).first()).toBeVisible();
});

test('real issue benchmark can load a case and run it on CUDA', async ({page}) => {
  test.skip(process.env.LAYA_LIVE_TEST !== '1', 'Requires the local service.');
  test.setTimeout(180000);
  const key = readFileSync(new URL('../../.env', import.meta.url), 'utf8').match(/^LAYA_API_KEY=(.+)$/m)![1].trim();
  await page.setViewportSize({width: 1440, height: 1100});
  await page.goto('/');
  await page.getByLabel('API key', {exact:true}).fill(key);
  await page.getByRole('button', {name:'Connect', exact:true}).click();
  await expect(page.getByText('Authenticated for this tab')).toBeVisible();
  await page.getByRole('button', {name:'Real benchmark', exact:true}).click();
  await expect(page.getByRole('heading', {name:'Your issues, your GPU'})).toBeVisible();
  await expect(page.locator('.benchmark-table')).toContainText('225 / 233');
  await expect(page.getByRole('heading', {name:'The trial now needs a credit card'})).toBeVisible();
  await page.screenshot({path:'test-results/real-benchmark.png', fullPage:true});
  await page.getByRole('button', {name:'Try this example'}).first().click();
  await expect(page.getByLabel('State input')).toContainText('nodemailer');
  await page.getByRole('button', {name:'Run decision'}).click();
  await expect(page.locator('.answers .answer')).toHaveCount(1, {timeout:150000});
  await expect(page.locator('.choice-description')).toContainText(/dependency/i);
  await expect(page.locator('.result-meta')).toContainText('cuda:0');
  await page.getByRole('button', {name:'Real benchmark', exact:true}).click();
  await page.setViewportSize({width:390, height:844});
  await page.emulateMedia({reducedMotion:'reduce'});
  await expect(page.getByRole('heading', {name:'Your issues, your GPU'})).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({path:'test-results/real-benchmark-mobile.png', fullPage:true});
});

test('Decision lab replays the full fixed study through the real CUDA worker', async ({page}) => {
  test.skip(process.env.LAYA_LIVE_TEST !== '1', 'Requires the local service.');
  test.setTimeout(300000);
  const key = readFileSync(new URL('../../.env', import.meta.url), 'utf8').match(/^LAYA_API_KEY=(.+)$/m)![1].trim();
  const errors: string[] = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.setViewportSize({width:1440, height:1100});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto('/batch#decision-lab');
  await page.getByLabel('API key', {exact:true}).fill(key);
  await page.getByRole('button', {name:'Connect', exact:true}).click();
  await expect(page.locator('.lab-kpis')).toContainText('390');
  await page.locator('.lab-comparison').screenshot({path:'test-results/decision-lab-saved-real.png'});
  await page.getByRole('button', {name:'Run selected tests', exact:true}).click();
  await expect(page.getByText('Replay complete', {exact:true})).toBeVisible({timeout:240000});
  await expect(page.locator('.lab-kpis')).toContainText('390');
  const download = page.waitForEvent('download');
  await page.getByRole('button', {name:'Export results', exact:true}).click();
  const file = await download;
  const result = JSON.parse(readFileSync((await file.path())!, 'utf8'));
  expect(result.status).toBe('completed');
  expect(result.records).toHaveLength(390);
  expect(result.warmups).toHaveLength(3);
  expect(result.request_sha256).toBe(JSON.parse(readFileSync(new URL('../../docs/benchmark/everyday-baseline.json', import.meta.url), 'utf8')).request_sha256);
  expect(result.records.every((r: {valid: boolean; device: string}) => r.valid && r.device === 'cuda:0')).toBe(true);
  expect(errors).toEqual([]);
  mkdirSync(new URL('../../data/verification/', import.meta.url), {recursive:true});
  writeFileSync(new URL('../../data/verification/decision-lab-live.json', import.meta.url), JSON.stringify(result, null, 2));
  await page.locator('.lab-comparison').screenshot({path:'test-results/decision-lab-live-real.png'});
  await page.locator('.decision-lab').screenshot({path:'test-results/decision-lab-live-full.png'});
});
