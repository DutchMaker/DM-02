const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const origin='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020';
const base=origin+'/build/experiments/2026-11-15-analog-integrated/';
const output=path.join(__dirname,'../experiments/2026-11-15-analog-integrated');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   const report=await(await context.request.get(base+'report.json')).json();
   assert.equal(report.state,'complete');assert.deepEqual(report.checks.filter(r=>r.status==='error'),[]);
   assert.deepEqual(report.milestones.map(m=>[m.passed,m.total]),[[3,5],[3,5],[8,9]]);
   assert.equal(await page.locator('#checks tbody tr').count(),report.checks.length);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   await page.screenshot({path:path.join(output,`${name}.png`),fullPage:true});
   const state=await(await context.request.get(origin+'/api/state')).json();
   assert(state.freshness.fresh);assert.deepEqual(state.freshness.altered_evidence,[]);
   assert.equal(state.report.finished_at,report.finished_at);
   assert.equal((await page.goto(origin+'/',{waitUntil:'networkidle'})).status(),200);
   await page.locator('#check-analog').waitFor();
   assert.equal(await page.locator('#check-analog .badge').innerText(),'pass');
   assert.equal(await page.locator('#check-analog-rc .badge').innerText(),'limited');
   assert.match(await page.locator('#check-analog').innerText(),/65\.389 ns/);
   assert.match(await page.locator('#freshness').innerText(),/SOURCE & EVIDENCE CURRENT/);
   const milestone=page.locator('#milestones .milestone').nth(1);
   assert.match(await milestone.innerText(),/3\/5/);
   const links=await page.locator('#check-analog .links a').evaluateAll(ns=>ns.map(n=>n.href));
   assert.equal(links.filter(p=>p.endsWith('.csv')).length,10);
   for(const link of links)assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(output,`live-${name}.png`),fullPage:true});assert.deepEqual(errors,[]);
   results.push({viewport:name,passed:true,checks:report.checks.length,analog_links:links.length,source_and_evidence_current:true,errors});await context.close();
  }
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
