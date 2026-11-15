const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/experiments/2026-11-15-refreshed-complete/';
const output=path.join(__dirname,'../experiments/2026-11-15-refreshed-complete');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   const report=await(await context.request.get(base+'report.json')).json();
   assert.equal(report.state,'complete');assert(report.finished_at);
   assert.deepEqual(report.checks.filter(r=>r.status==='error'),[]);
   assert.deepEqual(report.checks.filter(r=>r.status==='fail').map(r=>r.id),['timing']);
   assert.deepEqual(report.milestones.map(m=>[m.passed,m.total]),[[3,5],[2,5],[8,9]]);
   assert.equal(await page.locator('#checks tbody tr').count(),report.checks.length);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   for(const name of ['archive.json','manifest.json','boot/summary.json','distribution/summary.json'])
    assert.equal((await context.request.get(base+name)).status(),200,name);
   await page.screenshot({path:path.join(output,`${name}.png`),fullPage:true});assert.deepEqual(errors,[]);
   results.push({viewport:name,passed:true,checks:report.checks.length,errors});await context.close();
  }
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
