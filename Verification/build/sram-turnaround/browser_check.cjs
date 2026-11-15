const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/sram-turnaround/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   assert.match(await page.locator('#verdict').innerText(),/turnaround remains unqualified/);
   const result=await(await context.request.get(base+'review.json')).json();
   assert.equal(result.status,'limited');assert.equal(result.simulation_performed,false);
   assert.equal(result.results.ME1.buses.length,8);assert.equal(result.pin_mutations.length,3);
   assert.equal(result.results.ME1.turnaround_qualified,false);
   assert.deepEqual(result.results.ME1.conditional_blank_requirement_ns,{read_to_write:56.5,write_to_read:58});
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
