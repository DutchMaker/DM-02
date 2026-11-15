// Optional real-browser regression: NODE_PATH=/path/to/node_modules node Verification/emulator-browser.cjs
const {chromium}=require('playwright');
const http=require('node:http');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../Code/Emulator');
const server=http.createServer((req,res)=>{
  const pathname=decodeURIComponent(new URL(req.url,'http://localhost').pathname);
  const file=path.resolve(root,'.'+(pathname==='/'?'/index.html':pathname));
  if(!file.startsWith(root+path.sep)) {res.writeHead(403);res.end();return;}
  fs.readFile(file,(error,data)=>{
    if(error) {res.writeHead(404);res.end();return;}
    res.setHeader('Content-Type',({'.html':'text/html','.js':'text/javascript','.css':'text/css'})[path.extname(file)]||'application/octet-stream');
    res.end(data);
  });
});
(async()=>{
  await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
  let browser;
  const results=[];
  try {
    browser=await chromium.launch({channel:'chrome',headless:true});
    const bitmapText=fs.readFileSync(path.resolve(__dirname,'../Code/Assembler/programs/emulator_demo/emulator_demo_data.asm'),'utf8');
    const bitmap=[...bitmapText.matchAll(/\$([0-9a-f]{2})/gi)].map(m=>parseInt(m[1],16));
    // The source contains 16,382 pixels (the last row has two absent pixels).
    // Its separate $FF terminator belongs to emulator_demo.asm, not the raster.
    assert.ok(bitmap.length>0 && bitmap.length<=128*128);
    assert.ok(bitmap.every(pixel=>pixel===0||pixel===1));
    for(const name of ['hello_world','emulator_demo']) {
      const page=await browser.newPage();
      const errors=[];page.on('pageerror',e=>errors.push(e.message));
      await page.goto(`http://127.0.0.1:${server.address().port}/`);
      await page.waitForFunction(()=>window.emulator?.ui.objects.videodisplay.pixeldata.data);
      const bytes=Array.from(fs.readFileSync(path.join(root,'programs',name+'.bin')));
      if(name==='emulator_demo') {
        const start=Buffer.from(bytes).indexOf(Buffer.from(bitmap));
        assert.ok(start>=0,'Demo binary does not contain the source bitmap');
        assert.equal(bytes[start+bitmap.length],255,'Bitmap must terminate before instruction bytes');
      }
      const result=await page.evaluate(({bytes,bitmap,name})=>{
        emulator.load_program_binary(new Uint8Array(bytes));
        emulator.reset();emulator.state.halt=false;emulator.running=true;
        let steps=0;
        while(!emulator.state.halt && steps<1000000) {emulator.emulate();steps++;}
        emulator.ui.update();emulator.running=false;
        let pixelErrors=0;
        const display=emulator.ui.objects.videodisplay;
        const pixels=display.context.getImageData(0,0,display.width,display.height).data;
        if(name==='emulator_demo') {
          for(let y=0;y<display.height;y++) for(let x=0;x<display.width;x++) {
            const expected=x<128&&y<128&&bitmap[y*128+x]===1?255:0;
            const index=(y*display.width+x)*4;
            if([0,1,2,3].some(c=>pixels[index+c]!==expected)) pixelErrors++;
          }
        }
        return {name,halted:emulator.state.halt,steps,text:emulator.ui.objects.textdisplay.data,
                pixelErrors,pixelsChecked:name==='emulator_demo'?display.width*display.height:0};
      },{bytes,bitmap,name});
      assert.equal(result.halted,true,`${name} did not halt`);
      assert.equal(result.text,'Hello world\r:-)',`${name} text output`);
      assert.equal(result.pixelErrors,0,`${name} canvas differs from source bitmap`);
      assert.deepEqual(errors,[]);
      await page.screenshot({path:path.join(__dirname,'build',name+'-browser.png')});
      results.push({...result,status:'pass'});
      await page.close();
    }
    const evidence={status:'pass',bitmapSourcePixels:bitmap.length,scope:'Actual browser CPU, memory, IO and canvas running the two committed demo binaries; source bitmap and transparent remainder checked pixel-for-pixel.',results};
    fs.writeFileSync(path.join(__dirname,'build/emulator-browser.json'),JSON.stringify(evidence,null,2)+'\n');
    console.log(JSON.stringify(evidence));
  } finally {
    if(browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
