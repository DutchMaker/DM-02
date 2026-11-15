const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/dip-logic/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   assert.equal(await page.locator('#replacements tbody tr').count(),6);
   assert.match(await page.locator('#scope').innerText(),/zero SOIC/);
   assert.match(await page.locator('#scope').innerText(),/integrated timing and physical qualification are pending/);
   assert.match(await page.locator('#scope').innerText(),/Eight PLCC/);
   assert.match(await page.locator('#stock-update').innerText(),/Zero CD74ACT175E owned/);
   const replacements=await page.locator('#replacements').innerText();
   for(const part of ['74HCT154N','CD74HCT161E','SN74HC377N','SN74HCT00N','SN74HCT08N'])assert(replacements.includes(part));
   const summary=await(await context.request.get(base+'summary.json')).json();
   assert(summary.passed);assert.equal(summary.changed_packages,91);assert.equal(summary.remaining_soic,0);
   assert.equal(summary.boards.length,14);assert.equal(summary.integrated_timing_qualified,false);
   assert.equal(summary.faults.length,4);assert(summary.faults.every(f=>f.detected));
   const workbook=await(await context.request.get(base+'workbook-validation.json')).json();
   assert(workbook.passed);assert.equal(workbook.remaining_plcc,8);
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href));
   for(const link of links)assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   assert.deepEqual(errors,[]);await page.screenshot({path:path.join(__dirname,name+'.png'),fullPage:true});
   results.push({viewport:name,passed:true,links:links.length});await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
