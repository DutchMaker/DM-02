const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/experiments/2026-11-15-analog-timeout/';
const output=path.join(__dirname,'../experiments/2026-11-15-analog-timeout');
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('.error').innerText(),/harness error/);
   const report=await(await context.request.get(base+'report.json')).json();
   assert.equal(report.state,'complete');
   assert.deepEqual(report.checks.filter(r=>r.status==='error').map(r=>r.id),['alu-sequences']);
   assert.deepEqual(report.milestones.map(m=>[m.passed,m.total]),[[3,5],[3,5],[7,9]]);
   const archive=await(await context.request.get(base+'archive.json')).json();assert.equal(archive.acceptance_complete,false);
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href));
   for(const link of links)assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert.deepEqual(errors,[]);await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
   results.push({viewport:name,passed:true,links:links.length,error_retained:true});await context.close();
  }
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
