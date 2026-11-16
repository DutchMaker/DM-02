const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020';
const promoted=process.argv.includes('--promoted');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true}),results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport}),page=await context.newPage(),errors=[];
   page.on('pageerror',e=>errors.push(e.message));
   assert.equal((await page.goto(base+'/build/cp1-hct273/',{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#state').innerText(),/Complete digital rerun passed/);
   assert.match(await page.locator('#boot').innerText(),/2,840,175 microcycles/);
   const accepted=await(await context.request.get(base+'/build/cp1-hct273/acceptance.json')).json();
   assert(accepted.passed && accepted.full_digital_rerun && !accepted.physical_qualification);
   assert.equal(accepted.selected_273,'CD74HCT273E');assert.equal(accepted.boot_hold_observations.length,3);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href));
   for(const link of new Set(links))assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   if(promoted){
    assert.equal((await page.goto(base+'/',{waitUntil:'networkidle'})).status(),200);
    await page.waitForFunction(()=>document.querySelector('#freshness').textContent.includes('SOURCE & EVIDENCE CURRENT'));
    const state=await(await context.request.get(base+'/api/state')).json();
    assert(state.freshness.fresh);assert.equal(state.report.revision,'CP1-R2');
    assert.deepEqual(state.report.milestones.map(m=>m.passed),[3,3,8]);
    assert.equal(state.report.checks.filter(c=>c.status==='error').length,0);
    assert(state.report.checks.some(c=>c.id==='component-specification' && c.status==='pass'));
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   }
   assert.deepEqual(errors,[]);
   await page.screenshot({path:path.join(__dirname,(promoted?'dashboard-':'')+name+'.png'),fullPage:true});
   results.push({viewport:name,passed:true,links:new Set(links).size});await context.close();
  }
  const result={passed:true,promoted,results};
  fs.writeFileSync(path.join(__dirname,promoted?'dashboard-check.json':'browser-check.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
