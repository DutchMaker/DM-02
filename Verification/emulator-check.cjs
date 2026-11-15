// Execute the actual instruction engine with deterministic memory and no DOM.
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const document = {getElementById: () => ({addEventListener() {}}), write() {}, addEventListener() {}};
const context = vm.createContext({console, document});
for (const file of ['emulator.js', 'instructions_logic.js']) {
  vm.runInContext(fs.readFileSync(path.join(root, 'Code/Emulator/js', file), 'utf8'), context);
}
const e = context.emulator;
const realMemoryGet=e.state.memory.get,realMemorySet=e.state.memory.set;
const rows=[];
function test(name, program, setup, check) {
  const memory = new Uint8Array(65536); memory.set(program);
  Object.assign(e.state, {pc:0, sp:0x8000, halt:false});
  Object.assign(e.state.registers, {a:0,b:0,c:0,h:0,l:0,ir:0});
  e.state.flags.clear();
  e.state.memory.get = address => memory[address & 65535];
  e.state.memory.set = (address, data) => { memory[address & 65535] = data; };
  e.halt = () => {e.state.halt=true;};
  setup(e.state, memory);
  let steps=0, error;
  try { while(!e.state.halt && steps++<100) e.emulate(); }
  catch (err) {error=String(err);}
  const result=check(e.state, memory);
  rows.push({name, status: !error && e.state.halt && result.actual===result.expected ? 'pass':'fail', steps, ...result, error});
}
test('MOV immediate / ADD / HALT', [0x17,12,0x18,7,0x54,0xe2], ()=>{}, s=>({expected:19,actual:s.registers.a}));
test('8-bit addition wraps: 250 + 10', [0x17,250,0x58,10,0xe2], ()=>{}, s=>({expected:4,actual:s.registers.a}));
test('8-bit subtraction wraps: 1 - 3', [0x17,1,0x6a,3,0xe2], ()=>{}, s=>({expected:254,actual:s.registers.a}));
test('Signed overflow: 127 + 1', [0x17,127,0x58,1,0xe2], ()=>{}, s=>({expected:1,actual:s.flags.o}));
test('PUSH A / clear A / POP A round trip', [0x17,0x5a,0x43,0x17,0,0x4b,0xe2], ()=>{}, s=>({expected:0x5a,actual:s.registers.a}));
test('Two-byte stack round trip', [0x1c,0x12,0x34,0x48,0x1c,0,0,0x50,0xe2], ()=>{}, s=>({expected:0x1234,actual:s.registers.b*256+s.registers.c}));
test('XOR immediate', [0x17,0xaa,0x95,0xff,0xe2], ()=>{}, s=>({expected:0x55,actual:s.registers.a}));

// Reuse one memory image for exhaustive single-instruction tests.
const memory=new Uint8Array(65536);
e.state.memory.get=address=>memory[address & 65535];
e.state.memory.set=(address,data)=>{memory[address & 65535]=data;};
function execute(op,a,b,carry=0) {
  memory[0]=op;
  Object.assign(e.state,{pc:0,halt:false});
  Object.assign(e.state.registers,{a,b,c:b,h:b,l:b});
  Object.assign(e.state.flags,{c:carry,z:1,o:1,n:1});
  e.emulate();
}
function actualWord(value=e.state.registers.a) {
  const f=e.state.flags;
  return value | f.c<<8 | f.o<<9 | f.z<<10 | f.n<<11;
}
function word(value,carry=0,overflow=0,stored=value) {
  return stored | carry<<8 | overflow<<9 | Number(value===0)<<10 | Number(value>=128)<<11;
}
function signed(n) {return n<128?n:n-256;}
function group(name,body) {
  let checked=0,failures=0; const examples=[];
  body((actual,expected,input)=>{
    checked++;
    if(actual!==expected) {
      failures++;
      if(examples.length<4) examples.push({...input,actual,expected});
    }
  });
  rows.push({name,status:failures?'fail':'pass',checked,failures,examples});
}
for(const [name,op,subtract,withCarry,compare] of [
  ['ADD',0x54,false,false,false],['ADC',0x5d,false,true,false],
  ['SUB',0x66,true,false,false],['SBC',0x6f,true,true,false],['CMP',0xbb,true,false,true]
]) {
  group(`${name} B: every operand and incoming carry`,check=>{
    for(let a=0;a<256;a++) for(let b=0;b<256;b++) for(let c=0;c<2;c++) {
      execute(op,a,b,c);
      const extra=withCarry?c:0;
      const raw=subtract?a-b-extra:a+b+extra;
      const signedRaw=subtract?signed(a)-signed(b)-extra:signed(a)+signed(b)+extra;
      const value=((raw%256)+256)%256;
      const expected=word(value,Number(raw<0||raw>255),Number(signedRaw < -128||signedRaw>127),compare?a:value);
      check(actualWord(),expected,{a,b,c});
    }
  });
}
for(const [name,op,operation] of [
  ['AND',0x81,(a,b)=>a&b],['OR',0x89,(a,b)=>a|b],['XOR',0x91,(a,b)=>a^b],
  ['NOT',0x9a,(a,b)=>255-b],['SHL',0xa2,(a,b)=>a*2**b],['SHR',0xa7,(a,b)=>Math.floor(a/2**b)],
  ['ASR',0xac,(a,b)=>(Math.floor(signed(a)/2**b)+256)%256],
  ['ROL',0xb1,(a,b)=>((a*2**(b%8))+Math.floor(a/2**(8-b%8)))%256],
  ['ROR',0xb6,(a,b)=>(Math.floor(a/2**(b%8))+(a%2**(b%8))*2**(8-b%8))%256]
]) {
  group(`${name} B: all 65536 operand pairs`,check=>{
    for(let a=0;a<256;a++) for(let b=0;b<256;b++) {
      execute(op,a,b,1);
      const raw=operation(a,b),value=raw%256;
      check(actualWord(name==='NOT'?e.state.registers.b:e.state.registers.a),word(value,name==='SHL'?Math.floor(raw/256)%2:0),{a,b});
      if(name==='NOT') check(e.state.registers.a,a,{a,b,preserved:'A'});
    }
  });
}
for(const [index,reg] of ['a','b','c','h','l'].entries()) {
  group(`NOT ${reg.toUpperCase()}: named destination, flags and preserved registers`,check=>{
    for(let value=0;value<256;value++) {
      memory[0]=0x99+index;
      Object.assign(e.state,{pc:0,halt:false});
      Object.assign(e.state.registers,{a:0x17,b:0x28,c:0x39,h:0x4a,l:0x5b});
      e.state.registers[reg]=value;
      const before={...e.state.registers};
      Object.assign(e.state.flags,{c:1,z:1,o:1,n:1});
      e.emulate();
      check(actualWord(e.state.registers[reg]),word(255-value),{reg,value});
      for(const other of ['a','b','c','h','l'].filter(r=>r!==reg)) {
        check(e.state.registers[other],before[other],{reg,value,preserved:other});
      }
    }
  });
}
for(const [name,first,delta] of [['INC',0x77,1],['DEC',0x7c,-1]]) {
  for(const [index,reg] of ['a','b','c','h','l'].entries()) {
    group(`${name} ${reg.toUpperCase()}: all bytes and incoming carry`,check=>{
      for(let value=0;value<256;value++) for(let c=0;c<2;c++) {
        execute(first+index,value,value,c);
        const raw=value+delta, signedRaw=signed(value)+delta;
        const result=(raw+256)%256;
        check(actualWord(e.state.registers[reg]),word(result,Number(raw<0||raw>255),Number(signedRaw < -128||signedRaw>127)),{value,c});
        if(reg!=='a') check(e.state.registers.a,value,{value,c,unmodified:'A'});
      }
    });
  }
}
for(let flags=0;flags<16;flags++) {
  test(`PUSH F / clear / POP F: packed flags ${flags}`, [0x4a,0xe0,0xe1,0x52,0xe2],s=>{
    Object.assign(s.flags,{c:flags&1,z:flags>>2&1,o:flags>>1&1,n:flags>>3&1});
  },s=>({expected:flags,actual:s.flags.c|s.flags.o<<1|s.flags.z<<2|s.flags.n<<3}));
}
test('CALL / balanced stack operations / RET', [0xcc,0,6,0xe2,0,0,0x17,0x5a,0x43,0x17,0,0x4b,0xd5],()=>{},s=>({expected:'90,32768,4',actual:[s.registers.a,s.sp,s.pc].join(',')}));

// Addressing-mode integration: distinct source registers and pointer/data locations
// catch decoder bugs that exhaustive B-register arithmetic alone cannot expose.
const forms=['a','b','c','h','l','immediate','address','indirect','hl-memory'];
for(const [name,base,subtract,withCarry,compare] of [
  ['ADD',0x53,false,false,false],['ADC',0x5c,false,true,false],
  ['SUB',0x65,true,false,false],['SBC',0x6e,true,true,false],['CMP',0xbb,true,false,true]
]) {
  const modes=compare?forms.slice(1):forms;
  for(const [index,mode] of modes.entries()) for(const [a,b,carry] of [[0,0,0],[255,2,1],[127,1,0],[128,255,1]]) {
    const op=base+index;
    const operands=mode==='immediate'?[b]:mode==='address'?[0x41,0]:mode==='indirect'?[0x42,0]:[];
    const program=[op,...operands,0xe2];
    const rhs=mode==='a'?a:b, extra=withCarry?carry:0;
    const raw=subtract?a-rhs-extra:a+rhs+extra;
    const sr=subtract?signed(a)-signed(rhs)-extra:signed(a)+signed(rhs)+extra;
    const value=(raw+512)%256;
    const expected=word(value,Number(raw<0||raw>255),Number(sr < -128||sr>127),compare?a:value);
    test(`${name} ${mode}: ${a},${b},C=${carry}`,program,(s,m)=>{
      Object.assign(s.registers,{a,b:17,c:34,h:51,l:68});
      if(['b','c','h','l'].includes(mode)) s.registers[mode]=b;
      if(mode==='hl-memory') {s.registers.h=0x41;s.registers.l=0;}
      m[0x4100]=b; m[0x4200]=0x41; m[0x4201]=0;
      s.flags.c=carry;
    },s=>({expected:`${expected}:${program.length}`+(['address','indirect'].includes(mode)?':16640':''),
           actual:`${actualWord()}:${s.pc}`+(['address','indirect'].includes(mode)?`:${s.registers.h*256+s.registers.l}`:'')}));
  }
}
// All register stack encodings and nested call return-address preservation.
for(const [index,reg] of ['a','b','c','h','l'].entries()) {
  test(`PUSH/POP ${reg.toUpperCase()} preserves stack pointer`,[0x43+index,0x17+index,0,0x4b+index,0xe2],s=>{
    s.registers[reg]=0x96;
  },s=>({expected:'150:32768',actual:`${s.registers[reg]}:${s.sp}`}));
}
test('Nested CALL/RET returns in LIFO order',[0xcc,0,6,0xe2,0,0,0xcc,0,10,0xd5,0x17,0x6b,0xd5],()=>{},s=>({expected:'107:32768:4',actual:`${s.registers.a}:${s.sp}:${s.pc}`}));
for(const [name,direct,indirect,operation] of [
  ['AND',0x86,0x87,(a,b)=>a&b],['OR',0x8e,0x8f,(a,b)=>a|b],
  ['XOR',0x96,0x97,(a,b)=>a^b],['NOT',0x9f,0xa0,(a,b)=>255-b]
]) for(const op of [direct,indirect]) {
  group(`${name} address form ${op.toString(16)}: result, flags and HL scratch`,check=>{
    for(let value=0;value<256;value++) {
      const mem=new Uint8Array(65536),target=0x41ff,address=op===direct?target:0x4200;
      mem.set([op,address>>8,address&255],0x2000);
      mem[0x4200]=target>>8;mem[0x4201]=target&255;mem[target]=value;
      Object.assign(e.state,{pc:0x2000,sp:0x9000,halt:false});
      Object.assign(e.state.registers,{a:0x96,b:0x63,c:0xa1,h:0x52,l:0xab});
      Object.assign(e.state.flags,{c:1,o:1,z:1,n:1});
      e.state.memory.get=address=>mem[address&65535];e.state.memory.set=(address,v)=>{mem[address&65535]=v;};
      e.emulate();
      check(actualWord(),word(operation(0x96,value)),{value});
      check(e.state.registers.h*256+e.state.registers.l,target,{value,field:'HL'});
      check(e.state.registers.b*256+e.state.registers.c,0x63a1,{value,field:'BC'});
      check(e.state.pc,0x2003,{value,field:'PC'});
    }
  });
}
for(let op=0xc3;op<=0xd4;op++) {
  group(`Branch ${op.toString(16)}: conditions, target and HL scratch`,check=>{
    for(let flags=0;flags<16;flags++) for(const pc of [0x1200,0x12fd,0x12fe]) for(const sameTarget of [false,true]) {
      const target=sameTarget?pc+3:0x4567,mem=new Uint8Array(65536);
      mem[pc]=op;mem[pc+1]=target>>8;mem[pc+2]=target&255;
      Object.assign(e.state,{pc,sp:0x9000,halt:false});
      Object.assign(e.state.registers,{a:0x96,b:0x63,c:0xa1,h:0x52,l:0xab});
      Object.assign(e.state.flags,{c:flags&1,o:flags>>1&1,z:flags>>2&1,n:flags>>3&1});
      const tests=[flags&1,flags&4,flags&8,flags&2,!(flags&1),!(flags&4),!(flags&8),!(flags&2)];
      const taken=op===0xc3||op===0xcc||!!tests[op<0xcc?op-0xc4:op-0xcd];
      const writes=[];
      e.state.memory.get=address=>mem[address&65535];
      e.state.memory.set=(address,v)=>{writes.push([address&65535,v]);mem[address&65535]=v;};
      e.emulate();
      check(e.state.pc,taken?target:pc+3,{flags,pc,target,field:'PC'});
      check(e.state.registers.h*256+e.state.registers.l,taken?target:0x52ab,{flags,pc,target,field:'HL'});
      check([e.state.registers.a,e.state.registers.b,e.state.registers.c].join(','),'150,99,161',{flags,pc,target,field:'ABC'});
      check(actualWord(0),flags<<8,{flags,pc,target,field:'flags'});
      const call=op>=0xcc&&taken;
      check(e.state.sp,call?0x8ffe:0x9000,{flags,pc,target,field:'SP'});
      check(JSON.stringify(writes),JSON.stringify(call?[[0x9000,(pc+1)>>8],[0x8fff,(pc+1)&255]]:[]),{flags,pc,target,field:'stack'});
    }
  });
}
group('Packed F ABI: every input byte, C/O/Z/N wiring and zero high nibble',check=>{
  for(let byte=0;byte<256;byte++) {
    const mem=new Uint8Array(65536);mem[0x2000]=0x52;mem[0x2001]=0x4a;mem[0x9000]=byte;
    Object.assign(e.state,{pc:0x2000,sp:0x8fff,halt:false});
    Object.assign(e.state.flags,{c:1,o:1,z:1,n:1});
    e.state.memory.get=addr=>mem[addr&65535];e.state.memory.set=(addr,v)=>{mem[addr&65535]=v;};
    e.emulate();
    check(actualWord(0),(byte&15)<<8,{byte,field:'POP flags'});
    check(e.state.sp,0x9000,{byte,field:'POP SP'});
    e.emulate();
    check(mem[0x9000],byte&15,{byte,field:'PUSH stored byte'});
    check(e.state.sp,0x8fff,{byte,field:'PUSH SP'});
  }
});
for(let op=0xd5;op<=0xdd;op++) {
  group(`Return ${op.toString(16)}: raw frame, conditions and wrapping`,check=>{
    for(let flags=0;flags<16;flags++) for(const saved of [0,1,0xff,0x100,0x12fe,0x12ff,0xfffd,0xfffe,0xffff]) {
      for(const sp of [0x8ffe,0xfffe,0xffff,0]) {
        const mem=new Uint8Array(65536);mem[0x2000]=op;
        mem[(sp+1)&65535]=saved&255;mem[(sp+2)&65535]=saved>>8;
        Object.assign(e.state,{pc:0x2000,sp,halt:false});
        Object.assign(e.state.registers,{a:0x96,b:0x63,c:0xa1,h:0x52,l:0xab});
        Object.assign(e.state.flags,{c:flags&1,o:flags>>1&1,z:flags>>2&1,n:flags>>3&1});
        const bits=[1,4,8,2],index=op-0xd6;
        const taken=op===0xd5 || (index<4?!!(flags&bits[index]):!(flags&bits[index-4]));
        let writes=0;
        e.state.memory.get=addr=>mem[addr&65535];e.state.memory.set=()=>{writes++;};
        e.emulate();
        check(e.state.pc,taken?(saved+2)&65535:0x2001,{flags,saved,sp,field:'PC'});
        check(e.state.sp,taken?(sp+2)&65535:sp,{flags,saved,sp,field:'SP'});
        check(actualWord(0),flags<<8,{flags,saved,sp,field:'flags'});
        check(['a','b','c','h','l'].map(r=>e.state.registers[r]).join(','),'150,99,161,82,171',{flags,saved,sp,field:'registers'});
        check(writes,0,{flags,saved,sp,field:'no writes'});
      }
    }
  });
}
group('CALL raw frame at operand-PC wrap boundaries',check=>{
  for(const pc of [0x12fe,0x12ff,0xfffd,0xfffe,0xffff]) {
    for(const sp of [0x9000,0,0xffff]) {
      const mem=new Uint8Array(65536);mem[pc]=0xcc;mem[(pc+1)&65535]=0x45;mem[(pc+2)&65535]=0x67;
      Object.assign(e.state,{pc,sp,halt:false});
      e.state.memory.get=addr=>mem[addr&65535];e.state.memory.set=(addr,v)=>{mem[addr&65535]=v;};
      e.emulate();
      const operand=(pc+1)&65535;
      check(mem[sp],operand>>8,{pc,sp,field:'stored high'});
      check(mem[(sp-1)&65535],operand&255,{pc,sp,field:'stored low'});
      check(e.state.sp,(sp-2)&65535,{pc,sp,field:'SP'});
      check(e.state.pc,0x4567,{pc,sp,field:'PC'});
    }
  }
});
group('Actual memory accessors wrap addresses before RAM/IO dispatch',check=>{
  e.state.memory.data=new Uint8Array(0xff00);
  const inputs=[],outputs=[];
  e.handle_input=addr=>{inputs.push(addr);return 0x5a;};
  e.handle_output=(addr,value)=>{outputs.push([addr,value]);};
  realMemorySet(0x10000,0x1ab);
  check(realMemoryGet(0),0xab,{field:'RAM byte and address wrapping'});
  check(realMemoryGet(0x20000),0xab,{field:'wrapped RAM read'});
  realMemorySet(-1,0x1cd);
  check(realMemoryGet(-1),0x5a,{field:'wrapped IO read'});
  check(JSON.stringify(inputs),'[65535]',{field:'IO input address'});
  check(JSON.stringify(outputs),'[[65535,205]]',{field:'IO output address and byte'});
});
// MOV contracts include documented scratch effects and every byte of memory.
// Mnemonics/lengths select test cases; expected effects do not use microcode.
const definitions=fs.readFileSync(path.join(root,'Code/Microcode/microcode.src'),'utf8')
  .split('.instructions')[1].split('.end')[0].trim().split('\n');
for(const definition of definitions) {
  const [hex,sizeText,nameText]=definition.trim().split(':');
  const name=nameText.trim();
  if(!name.startsWith('MOV ')) continue;
  const opcode=parseInt(hex,16),size=Number(sizeText),[dst,src]=name.slice(4).split(',');
  group(`${name}: destination, documented scratch effects and memory boundaries`,check=>{
    for(const target of [0x4100,0x41ff,0xffff]) for(const swap of [false,true]) {
      const mem=new Uint8Array(65536);
      for(let i=0;i<mem.length;i++) mem[i]=((i*37)^(i>>8)^0xa5)&255;
      const bc=swap?target:0x63a1,hl=swap?0x52ab:target;
      const regs={a:0x96,b:bc>>8,c:bc&255,h:hl>>8,l:hl&255};
      const operand=name.includes('(address)')?0x4200:target;
      mem[0x4200]=target>>8;mem[0x4201]=target&255;
      mem[0x2000]=opcode;mem[0x2001]=operand>>8;mem[0x2002]=operand&255;
      const wantMem=mem.slice(),want={...regs};
      const readWord=addr=>mem[addr&65535]*256+mem[(addr+1)&65535];
      const pair=s=>regs[s[0].toLowerCase()]*256+regs[s[1].toLowerCase()];
      const location=s=>s==='address'?operand:s==='(address)'?readWord(operand):pair(s.slice(1,-1));
      const width=['BC','HL'].includes(src)||['BC','HL'].includes(dst)?2:1;
      let value;
      if(['BC','HL'].includes(src)) value=pair(src);
      else if(/^[ABCHL]$/.test(src)) value=regs[src.toLowerCase()];
      else if(src==='value') value=width===2?operand:operand>>8;
      else value=width===2?readWord(location(src)):mem[location(src)];
      const putPair=(pair,n)=>{want[pair[0].toLowerCase()]=n>>8;want[pair[1].toLowerCase()]=n&255;};
      if(name.includes('address')) putPair(opcode===0x27?'BC':'HL',name.includes('(address)')?readWord(operand):operand);
      if(['BC','HL'].includes(dst)) putPair(dst,value);
      else if(/^[ABCHL]$/.test(dst)) want[dst.toLowerCase()]=value;
      else {
        const addr=location(dst);
        if(width===2) {wantMem[addr]=value>>8;wantMem[(addr+1)&65535]=value&255;}
        else wantMem[addr]=value;
      }
      Object.assign(e.state,{pc:0x2000,sp:0x9000,halt:false});
      Object.assign(e.state.registers,regs);
      Object.assign(e.state.flags,{c:1,o:1,z:0,n:1});
      e.state.memory.get=addr=>mem[addr&65535];e.state.memory.set=(addr,v)=>{mem[addr&65535]=v;};
      e.emulate();
      for(const reg of ['a','b','c','h','l']) check(e.state.registers[reg],want[reg],{target,swap,reg});
      check(Buffer.compare(mem,wantMem),0,{target,swap,field:'all memory'});
      check(e.state.pc,0x2000+size,{target,swap,field:'PC'});
      check(actualWord(0),0xb00,{target,swap,field:'preserved flags'});
    }
  });
}
console.log(JSON.stringify({scope:'Exhaustive arithmetic/comparison/logical/shift/rotate operand checks and INC/DEC bytes; all MOV encodings with documented scratch effects and memory boundaries; arithmetic addressing-mode boundaries, raw packed-F bytes, raw CALL/RET frames, conditional returns, wrapping and nested calls. Deterministic memory and stubbed DOM, plus actual memory-accessor wrapping checks; physical memory/IO coverage remains incomplete. V=0 outside signed arithmetic.',rows},null,2));
