const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cd1-decoupling/';
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const results=[];
  try {
    for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
      const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
      assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
      assert.equal(await page.locator('#feeds tbody tr').count(),3);
      assert.equal(await page.locator('#faults tbody tr').count(),5);
      assert.equal(await page.locator('#sources li').count(),5);
      assert.equal(await page.locator('figure img').count(),3);
      assert(await page.locator('figure img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0)));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      const links=await page.locator('a[href]').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.href))]);
      for(const url of links)assert.equal((await context.request.get(url)).status(),200,url);
      assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
      const summary=await(await context.request.get(base+'summary.json')).json();
      assert.equal(summary.fabrication_ready,false);assert.equal(summary.native_faults_drc_detected,4);
      assert.equal(summary.full_unformed_lead_pitch_fit,false);
      await page.screenshot({path:path.join(__dirname,`${name}.png`),fullPage:true});
      if(name==='desktop') {
        await page.locator('figure').first().screenshot({path:path.join(__dirname,'feed-plot.png')});
        await page.locator('.views').screenshot({path:path.join(__dirname,'cam-plots.png')});
      }
      const dashboard=await context.newPage();dashboard.on('pageerror',e=>errors.push(e.message));
      await dashboard.goto(new URL(base).origin,{waitUntil:'networkidle'});await dashboard.waitForSelector('#checks .check');
      const studies=await dashboard.locator('#layout-studies a').evaluateAll(nodes=>nodes.map(n=>n.href));
      assert.equal(studies.length,6);assert(studies.includes(base));
      for(const url of studies)assert.equal((await context.request.get(url)).status(),200,url);
      assert(await dashboard.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.match(await dashboard.locator('.release').innerText(),/Blocked/);
      const live=await(await context.request.get(new URL('/api/state',base).href)).json();
      assert.deepEqual(live.report.milestones.map(m=>[m.passed,m.total]),[[3,5],[2,5],[8,9]]);
      assert.equal(live.freshness.fresh,false);assert.equal(live.freshness.changed.length,10);
      const index=await(await context.request.get(new URL('/dashboard/index.html',base).href)).body();
      assert.equal(crypto.createHash('sha256').update(index).digest('hex'),summary.dashboard_index_sha256);
      assert.deepEqual(errors,[]);
      results.push({viewport:name,passed:true,links:links.length,feeds:3,fault_rows:5,sources:5,plots:3,dashboard_studies:6,stale_sources:10,errors});
      await context.close();
    }
    fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');
    console.log(JSON.stringify(results));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
