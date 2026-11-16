const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true}),results=[];
 try {
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
   const context=await browser.newContext({viewport}),page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   assert.equal((await page.goto(base+'/',{waitUntil:'networkidle'})).status(),200);
   await page.waitForFunction(()=>document.querySelector('#freshness').textContent.includes('SOURCE & EVIDENCE CURRENT'));
   assert.match(await page.locator('#release-requirements').innerText(),/CP1-RR1/);
   assert.match(await page.locator('#release-requirements').innerText(),/Physical release and hold remain unqualified/);
   const state=await(await context.request.get(base+'/api/state')).json();
   assert(state.freshness.fresh);assert.equal(state.report.revision,'CP1-R2');
   assert.equal(state.report.release_requirements.physical_qualification,false);
   assert.equal(state.report.release_requirements.native_truth_cases,8192);
   assert.equal(state.report.checks.find(c=>c.id==='release-requirements').status,'limited');
   assert.deepEqual(state.report.milestones.map(m=>m.passed),[3,3,8]);
   assert(!state.report.checks.some(c=>c.status==='error'));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert.equal((await page.goto(base+'/build/cp1-release/',{waitUntil:'networkidle'})).status(),200);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href).filter(h=>!h.includes('#')));
   for(const link of new Set(links))assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(__dirname,name+'.png'),fullPage:true});
   const plan=await(await context.request.get(base+'/build/cp1-release/measurement-plan.json')).json();
   assert.equal(plan.physical_qualification,false);assert.equal(plan.driver_cases.length,48);
   assert(plan.driver_cases.every(r=>r.actual_total_load_pf===null && r.actual_max_release_ns===null));
   assert.deepEqual(errors,[]);results.push({viewport:name,passed:true,links:new Set(links).size});
   await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');
  console.log(results);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
