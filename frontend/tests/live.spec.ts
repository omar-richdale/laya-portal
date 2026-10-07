// Opt in to a real GPU browser request; credentials are never saved in screenshots or traces.
import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

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
