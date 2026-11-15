const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/owned-inventory/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
    assert.equal(await page.locator('#parts tbody tr').count(),16);
   assert.match(await page.locator('#construction').innerText(),/no SOIC/);
   assert.match(await page.locator('#dip-bom').innerText(),/48 CD74ACT175E/);
   assert.match(await page.locator('#scope').innerText(),/not yet been simulated or promoted/);
   const stock=await(await context.request.get(base+'stock.json')).json();
    assert.equal(stock.parts.length,16);assert.equal(stock.allow_soic,false);
    assert.deepEqual(stock.parts.filter(p=>p.quantity!==null).map(p=>[p.reported_marking,p.quantity]),[['74HCT157',1],['CD74ACT175E',0]]);
    assert.equal(stock.parts.find(p=>p.reported_marking==='CD74ACT175E').owned,false);
    for(const part of ['74HCT154N','CD74HCT161E','SN74HC377N','SN74HCT00N','SN74HCT08N'])assert.equal(stock.parts.find(p=>p.reported_marking===part).owned,true);
    assert(!stock.parts.some(p=>p.reported_marking==='74HCT377'));
    assert.match(await page.locator('#stock-update').innerText(),/zero CD74ACT175E/);
    const review=await(await context.request.get(base+'logic-review.json')).json();
    assert.equal(review.hc377.inputs.length,20);
    assert.deepEqual(review.gates.max_delay_ns,{'SN74HCT00N':25,'SN74HCT08N':30});
   for(const marking of ['M27C322-100F1','M27C1024-10F1'])assert.equal(stock.parts.find(p=>p.reported_marking===marking).access_time_ns,100);
   assert.equal(stock.parts.find(p=>p.reported_marking==='MCP100-450D').package,'TO-92');
   const validation=await(await context.request.get(base+'validation.json')).json();
    assert(validation.passed);assert.equal(validation.changed_cells.length,46);
    assert.deepEqual(validation.known_owned_quantities,{'74HCT157':1,'CD74ACT175E':0});
    assert.deepEqual(validation.added_sheets,['DIP candidate guide','DIP candidate BOM','DIP substitutions','Reported stock']);
   assert.equal(validation.renamed_reference_sheet,'Reference FD1 BOM');
   assert.equal(validation.normal_sources_modified,false);
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
