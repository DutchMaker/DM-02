const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/clock-integration/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#verdict').innerText(),/150\/150 clock profiles/);
   assert.match(await page.locator('#verdict').innerText(),/158 regression tests/);
   assert.equal(await page.locator('#rejections tbody tr').count(),4);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const links=await page.locator('a[href]').evaluateAll(ns=>[...new Set(ns.map(n=>n.href))]);
   for(const link of links)assert.equal((await context.request.get(link)).status(),200,link);
   const summary=await(await context.request.get(base+'summary.json')).json();
   assert.equal(summary.status,'validated-in-staging');assert.equal(summary.physical_clock_qualified,false);
   assert.equal(summary.bom_change.published_workbook_modified,false);
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   await page.screenshot({path:path.join(__dirname,`${name}.png`),fullPage:true});assert.deepEqual(errors,[]);
   results.push({viewport:name,passed:true,links:links.length,tests:summary.tests,errors});await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
