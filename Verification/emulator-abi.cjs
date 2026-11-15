// Compare real instruction-engine state and writes with compiled-control fixtures.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const [input,output,mutation='none']=process.argv.slice(2);
const root=path.resolve(__dirname,'..');
const context=vm.createContext({console,document:{getElementById:()=>({addEventListener(){}}),write(){},addEventListener(){}}});
vm.runInContext(fs.readFileSync(path.join(root,'Code/Emulator/js/emulator.js'),'utf8'),context);
let source=fs.readFileSync(path.join(root,'Code/Emulator/js/instructions_logic.js'),'utf8');
function replace(before,after) {
  if(!source.includes(before)) throw new Error('Mutation anchor missing');
  source=source.replace(before,after);
}
if(mutation==='old-flags') {
  replace('emulator.state.flags.c | emulator.state.flags.o << 1 | emulator.state.flags.z << 2 | emulator.state.flags.n << 3',
          'emulator.state.flags.c << 3 | emulator.state.flags.o << 1 | emulator.state.flags.z << 2 | emulator.state.flags.n');
  replace('emulator.state.flags.c = byte & 1','emulator.state.flags.c = (byte >> 3) & 1');
  replace('emulator.state.flags.n = (byte >> 3) & 1','emulator.state.flags.n = byte & 1');
} else if(mutation==='old-call-return') {
  replace('var operand_pc = emulator.state.pc & 0xFFFF','var operand_pc = (emulator.state.pc + 2) & 0xFFFF');
  replace('((hi << 8) + lo + 2) & 0xFFFF','((hi << 8) + lo) & 0xFFFF');
} else if(mutation!=='none') throw new Error('Unknown mutation');
vm.runInContext(source,context);
const e=context.emulator,fixtures=JSON.parse(fs.readFileSync(input,'utf8'));
let failed=0;const examples=[],fields={};
for(const test of fixtures) {
  const mem=new Map(test.memory),writes=new Map();
  Object.assign(e.state,{pc:test.pc,sp:test.sp,halt:false});
  for(const [name,value] of Object.entries(test.registers)) e.state.registers[name.toLowerCase()]=value;
  Object.assign(e.state.flags,{c:test.flags&1,o:test.flags>>1&1,z:test.flags>>2&1,n:test.flags>>3&1});
  e.state.memory.get=addr=>{addr&=65535;return mem.has(addr)?mem.get(addr):((addr*37)^(addr>>8)^0xa5)&255;};
  e.state.memory.set=(addr,value)=>{addr&=65535;value&=255;mem.set(addr,value);writes.set(addr,value);};
  e.halt=()=>{e.state.halt=true;};
  e.emulate();
  const actual={registers:Object.fromEntries(['A','B','C','H','L'].map(r=>[r,e.state.registers[r.toLowerCase()]])),
                pc:e.state.pc,sp:e.state.sp,flags:e.state.flags.c|e.state.flags.o<<1|e.state.flags.z<<2|e.state.flags.n<<3,
                halted:e.state.halt,writes:[...writes].sort((a,b)=>a[0]-b[0])};
  const differences=Object.keys(actual).filter(k=>JSON.stringify(actual[k])!==JSON.stringify(test.expected[k]));
  if(differences.length) {
    failed++;
    for(const field of differences) fields[field]=(fields[field]||0)+1;
    if(examples.length<8) examples.push({id:test.id,differences,actual,expected:test.expected});
  }
}
fs.writeFileSync(output,JSON.stringify({mutation,cases:fixtures.length,failed,fields,examples},null,2)+'\n');
