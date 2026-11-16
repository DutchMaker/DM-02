const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020';
const output=path.join(__dirname,'../cp1-promotion');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   assert.equal((await page.goto(base+'/',{waitUntil:'networkidle'})).status(),200);
   await page.waitForFunction(()=>document.querySelector('#freshness').textContent.includes('SOURCE & EVIDENCE CURRENT'));
   assert.match(await page.locator('#run').innerText(),/CP1.*locked-evidence-replay/);
   const state=await(await context.request.get(base+'/api/state')).json();
   assert(state.freshness.fresh);assert.deepEqual(state.report.milestones.map(m=>m.passed),[3,3,8]);
   assert.equal(state.report.equivalence.model_hashes_compared,446);
   assert.equal(state.report.checks.filter(c=>c.status==='error').length,0);
   assert.match(await page.locator('#timing').innerText(),/HCT273/);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(output,name+'-dashboard.png'),fullPage:true});
   assert.equal((await page.goto(base+'/build/cp1-promotion/',{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#state').innerText(),/Physical qualification remains open/);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href));
   for(const link of new Set(links))assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
   await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
   assert.equal((await page.goto(base+'/build/cp1-timing-review/',{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#state').innerText(),/active CP1 remains unchanged/);
   const study=await(await context.request.get(base+'/build/cp1-timing-review/results.json')).json();
   assert(study.completed && !study.adopted);assert.equal(study.runs.length,8);
   assert(study.unit_checks.every(x=>x.detected));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
   await page.screenshot({path:path.join(output,'../cp1-timing-review',name+'.png'),fullPage:true});
   results.push({viewport:name,passed:true,links:new Set(links).size});await context.close();
  }
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(results);
  fs.writeFileSync(path.join(output,'../cp1-timing-review/browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
