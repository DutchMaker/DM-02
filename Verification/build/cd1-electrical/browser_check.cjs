const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');

const base = 'https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cd1-electrical/';

(async () => {
  const browser = await chromium.launch({channel: 'chrome', headless: true});
  const results = [];
  try {
    for (const [name, viewport] of [['desktop', {width: 1440, height: 1000}], ['mobile', {width: 390, height: 844}]]) {
      const context = await browser.newContext({viewport});
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
      const response = await page.goto(base, {waitUntil: 'networkidle'});
      assert.equal(response.status(), 200);
      assert.equal(await page.locator('#nets tbody tr').count(), 26);
      assert.equal(await page.locator('#sensitivity tbody tr').count(), 8);
      assert.equal(await page.locator('.plots img').count(), 4);
      assert(await page.locator('.plots img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0)));
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
      assert.equal(await page.locator('#comparison tbody tr').count(), 4);
      const links = await page.locator('a[href]').evaluateAll(nodes => [...new Set(nodes.map(node => node.href))]);
      const local = links.filter(url => url.startsWith(new URL(base).origin));
      for (const url of local) {
        const result = await context.request.get(url);
        assert.equal(result.status(), 200, url);
      }
      const remote = await context.request.get(base + 'remote-validation.json');
      assert((await remote.json()).passed);
      assert.deepEqual(errors, []);
      await page.screenshot({path: path.join(__dirname, `${name}.png`), fullPage: true});
      if (name === 'desktop') await page.locator('.plots').screenshot({path: path.join(__dirname, 'return-plots.png')});
      results.push({viewport: name, passed: true, local_links: local.length, signal_rows: 26, sensitivity_rows: 8, plots: 4, errors});
      await context.close();
    }
    fs.writeFileSync(path.join(__dirname, 'browser-check.json'), JSON.stringify({passed: true, base_url: base, results}, null, 2) + '\n');
    console.log(JSON.stringify(results));
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
