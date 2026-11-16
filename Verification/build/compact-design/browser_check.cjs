const {chromium}=require('playwright');
const fs=require('node:fs');const path=require('node:path');const assert=require('node:assert/strict');
const retry=process.argv.includes('--normal-retry');
const output=retry?path.join(__dirname,'../experiments/2026-11-15-analog-retry-timeout'):__dirname;
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/'+(retry?'experiments/2026-11-15-analog-retry-timeout':'compact-design')+'/';
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
 try{
  for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]] ){
   const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
   page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
   assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
   if(retry){
    const report=await(await context.request.get(base+'report.json')).json();
    assert.equal(report.state,'complete');
    assert.deepEqual(report.checks.filter(c=>c.status==='error').map(c=>c.id),['hardware-programs','boot']);
    assert.match(await page.locator('#state').innerText(),/Acceptance incomplete/);
   }else{
    const summary=await(await context.request.get(base+'summary.json')).json();
    assert.equal(summary.logic_memory_packages,192);assert.equal(summary.saving,96);
    assert(summary.all_logic_memory_dip);assert.equal(summary.physical_qualification,false);
    assert.equal(summary.interconnect.assembly_groups,230);assert.equal(summary.native_boards,12);
    if(process.argv.includes('--complete')){
     assert.equal(summary.digital_verification_passed,true);
     assert.equal(summary.state,'digital-verification-complete');
     assert.match(await page.locator('#boot-result').innerText(),/2,840,175 microcycles/);
     const acceptance=await(await context.request.get(base+'acceptance.json')).json();
     assert(acceptance.passed && acceptance.digital_only);assert.equal(acceptance.physical_qualification,false);
     const boot=summary.runs.find(r=>r.boot);assert(boot.passed && boot.boot_check.passed);
     assert.equal(boot.output.pixels_checked,48000);assert.equal(boot.output.pixel_errors,0);
    }
    assert.equal(await page.locator('#milestones tbody tr').count(),3);
    assert.match(await page.locator('#state').innerText(),/Physical electrical qualification remains open/);
   }
   assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
   const links=await page.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.href));
   for(const link of links)assert.equal((await context.request.get(link)).status(),200,link);
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));assert.deepEqual(errors,[]);
   await page.screenshot({path:path.join(output,name+'.png'),fullPage:true});
   results.push({viewport:name,passed:true,links:links.length});await context.close();
  }
  fs.writeFileSync(path.join(output,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(results);
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
