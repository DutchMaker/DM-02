const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/pilot-transient/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#verdict').innerText(),/5 V \/ 25 °C/);
   assert.match(await page.locator('#verdict').innerText(),/65\.389 ns/);
   for(const [id,count] of [['normal',2],['correlation',8],['independent',4],['faults',8]])
    assert.equal(await page.locator(`#${id} tbody tr`).count(),count);
   assert(await page.locator('img').evaluate(el=>el.complete&&el.naturalWidth>0));
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
   const links=await page.locator('a[href]').evaluateAll(ns=>[...new Set(ns.map(n=>n.href))]);
   const local=links.filter(link=>new URL(link).origin===new URL(base).origin);
   for(const link of local)assert.equal((await context.request.get(link)).status(),200,link);
   const acceptance=await(await context.request.get(base+'acceptance.json')).json();
   assert.equal(acceptance.requirement_status,'pass');assert.equal(acceptance.physical_clock_qualified,false);
   assert.equal(acceptance.full_operating_envelope_qualified,false);
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   await page.screenshot({path:path.join(__dirname,`${name}.png`),fullPage:true});assert.deepEqual(errors,[]);
   results.push({viewport:name,passed:true,local_links:local.length,positive_cases:2,faults:9,errors});await context.close();
  }
  fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
