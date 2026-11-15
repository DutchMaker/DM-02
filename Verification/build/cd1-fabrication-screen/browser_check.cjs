const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cd1-fabrication-screen/';

(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});
  const results=[];
  try {
    for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
      const context=await browser.newContext({viewport});
      const page=await context.newPage();
      const errors=[];
      page.on('pageerror',e=>errors.push(e.message));
      page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
      assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
      for(const [id,count] of [['scenarios',9],['facts',24],['rules',11],['holes',3]]) {
        assert.equal(await page.locator(`#${id} tbody tr`).count(),count,id);
      }
      assert.equal(await page.locator('figure img').count(),2);
      assert(await page.locator('figure img').evaluateAll(images=>images.every(i=>i.complete&&i.naturalWidth>0)));
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      const links=await page.locator('a[href]').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.href))]);
      const local=links.filter(url=>url.startsWith(new URL(base).origin));
      for(const url of local)assert.equal((await context.request.get(url)).status(),200,url);
      assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
      const summary=await(await context.request.get(base+'summary.json')).json();
      assert.equal(summary.fabrication_ready,false);
      assert.equal(summary.acceptance_changed,false);
      assert.equal(summary.equivalent_loads.length,54);
      assert.equal(summary.longest_root_scenarios_over_5pf,5);
      assert.deepEqual(errors,[]);
      await page.screenshot({path:path.join(__dirname,`${name}.png`),fullPage:true});
      if(name==='desktop')await page.locator('.views').screenshot({path:path.join(__dirname,'cam-plots.png')});
      const dashboard=await context.newPage();
      dashboard.on('pageerror',e=>errors.push(e.message));
      await dashboard.goto(new URL(base).origin,{waitUntil:'networkidle'});
      await dashboard.waitForSelector('#checks .check');
      assert.equal(await dashboard.locator('#layout-studies a').count(),5);
      const studyLinks=await dashboard.locator('#layout-studies a').evaluateAll(nodes=>nodes.map(n=>n.href));
      assert(studyLinks.includes(base));
      for(const url of studyLinks)assert.equal((await context.request.get(url)).status(),200,url);
      assert(await dashboard.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      assert.match(await dashboard.locator('.release').innerText(),/Blocked/);
      const live=await(await context.request.get(new URL('/api/state',base).href)).json();
      assert.deepEqual(live.report.milestones.map(m=>[m.passed,m.total]),[[3,5],[2,5],[8,9]]);
      assert.equal(live.freshness.fresh,false);
      const index=await(await context.request.get(new URL('/dashboard/index.html',base).href)).body();
      assert.equal(crypto.createHash('sha256').update(index).digest('hex'),summary.dashboard_index_sha256);
      assert.deepEqual(errors,[]);
      results.push({viewport:name,passed:true,local_links:local.length,scenarios:9,facts:24,rules:11,hole_groups:3,plots:2,dashboard_study_links:5,normal_report_fresh:live.freshness.fresh,changed_sources:live.freshness.changed,errors});
      await context.close();
    }
    fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,base_url:base,results},null,2)+'\n');
    console.log(JSON.stringify(results));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
