const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const crypto=require('node:crypto');
const base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/bom-inventory/';
(async()=>{
  const browser=await chromium.launch({channel:'chrome',headless:true});const results=[];
  try {
    for(const [name,viewport] of [['desktop',{width:1440,height:1000}],['mobile',{width:390,height:844}]]) {
      const context=await browser.newContext({viewport});const page=await context.newPage();const errors=[];
      page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
      assert.equal((await page.goto(base,{waitUntil:'networkidle'})).status(),200);
      const validation=await(await context.request.get(base+'validation.json')).json();assert(validation.passed);
      assert.equal(await page.locator('#current tbody tr').count(),19);
      assert.equal(await page.locator('#baseline tbody tr').count(),validation.baseline_ic_rows);
      assert.equal(await page.locator('article[id^="change-"]').count(),17);
      assert.equal(await page.locator('#tht tbody tr').count(),6);
      assert.equal(await page.locator('#options tbody tr').count(),8);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
      await page.locator('#assembly').selectOption('SMD');
      assert.equal(await page.locator('#current tbody tr:visible').count(),6);
      assert.equal(await page.locator('#current tbody tr:visible').evaluateAll(rows=>rows.reduce((n,r)=>n+Number(r.cells[1].textContent),0)),91);
      if(name==='desktop')await page.locator('#current').screenshot({path:path.join(__dirname,'smd-filter.png')});
      await page.locator('#assembly').selectOption('');await page.locator('#search').fill('UM61512');
      assert.equal(await page.locator('#current tbody tr:visible').count(),1);
      assert.match(await page.locator('#current tbody tr:visible').innerText(),/AS6C1008/);
      await page.locator('#search').fill('not-a-real-chip');assert.equal(await page.locator('#current tbody tr:visible').count(),0);
      await page.locator('#search').fill('');
      const links=await page.locator('a[href]').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.href))]);
      for(const url of links){
        const parsed=new URL(url);
        if(parsed.hash){assert.equal(await page.locator(parsed.hash).count(),1);continue;}
        assert.equal((await context.request.get(url)).status(),200,url);
      }
      const filename='DM-02-working-BOM-and-inventory.xlsx';
      const download=await Promise.all([page.waitForEvent('download'),page.locator(`a[href="${filename}"]`).click()]);
      assert.equal(download[0].suggestedFilename(),filename);assert.equal(await download[0].failure(),null);
      const downloaded=fs.readFileSync(await download[0].path());const local=fs.readFileSync(path.join(__dirname,filename));
      assert.equal(crypto.createHash('sha256').update(downloaded).digest('hex'),crypto.createHash('sha256').update(local).digest('hex'));
      assert((await(await context.request.get(base+'remote-validation.json')).json()).passed);
      await page.screenshot({path:path.join(__dirname,`${name}.png`),fullPage:true});
      assert.deepEqual(errors,[]);results.push({viewport:name,passed:true,current_ic_types:19,smd_types:6,smd_packages:91,
        baseline_ic_rows:validation.baseline_ic_rows,changes:17,links:links.length,download_hash_matches:true,errors});
      await context.close();
    }
    fs.writeFileSync(path.join(__dirname,'browser-check.json'),JSON.stringify({passed:true,results},null,2)+'\n');console.log(JSON.stringify(results));
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
