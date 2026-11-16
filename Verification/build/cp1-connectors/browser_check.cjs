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
   assert.match(await page.locator('#mechanical-contract').innerText(),/CP1-MC1/);
   assert.match(await page.locator('#mechanical-contract').innerText(),/qualification pending/);
   const state=await(await context.request.get(base+'/api/state')).json();
   assert(state.freshness.fresh);assert.equal(state.report.revision,'CP1-R2');
   assert.equal(state.report.mechanical_contract.owner_approved,true);
   assert.equal(state.report.checks.find(c=>c.id==='connector-plan').status,'limited');
   assert.deepEqual(state.report.milestones.map(m=>m.passed),[3,3,8]);
   assert(!state.report.checks.some(c=>c.status==='error'));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   await page.screenshot({path:path.join(__dirname,name+'.png'),fullPage:true});
   assert.equal((await page.goto(base+'/build/cp1-connectors/',{waitUntil:'networkidle'})).status(),200);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href).filter(h=>!h.includes('#')));
   for(const link of new Set(links))assert.equal((await context.request.get(link)).status(),200,link);
   assert.equal((await page.goto(base+'/build/cp1-connectors/contacts.html',{waitUntil:'networkidle'})).status(),200);
   assert.equal(await page.locator('table').count(),14);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const check=await(await context.request.get(base+'/build/cp1-connectors/check.json')).json();
   assert(check.passed&&!check.physical_qualification);assert.equal(check.contacts_checked,1242);
   assert.deepEqual(errors,[]);results.push({viewport:name,passed:true,links:new Set(links).size});
   await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');
  console.log(results);
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
