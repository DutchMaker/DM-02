import json
from .common import BUILD, VROOT, command, evidence, write_json
from .legacy import connectivity


def emulator():
    code,log=command(['node',VROOT/'emulator-check.cjs'])
    (BUILD/'emulator.log').write_text(log)
    if code: raise RuntimeError(log)
    result=json.loads(log)
    write_json(BUILD/'emulator.json',result)
    rows=result['rows']; failures=sum(r['status']=='fail' for r in rows)
    checked=sum(r.get('checked',1) for r in rows)
    return evidence('emulator','Instruction-engine regression suite','fail' if failures else 'pass',
                    f'{checked:,} assertions in {len(rows)} groups; {failures} failing groups.',rows=rows,checked=checked,
                    artifacts=['emulator.json'],limitation=result['scope'])


def browser():
    code,log=command(['node',VROOT/'emulator-browser.cjs'],timeout=120)
    (BUILD/'emulator-browser.log').write_text(log)
    if code: raise RuntimeError(log)
    result=json.loads(log)
    return evidence('browser','Browser CPU and display regression',result['status'],
                    'Both demo binaries reach HALT with exact text output; 48,000 canvas pixels checked against the source bitmap.',
                    rows=result['results'],artifacts=['emulator-browser.json','emulator-browser.log','hello_world-browser.png','emulator_demo-browser.png'],
                    limitation=result['scope'])


def registers(sheet):
    folder=BUILD/'registers'; folder.mkdir(parents=True,exist_ok=True)
    nets=connectivity(sheet)
    refs={'U3':'A','U5':'B','U6':'C','U9':'H','U11':'L','U14':'IR'}
    mapping={}
    for ref,name in refs.items():
        c=next(c for c in sheet['components'] if c['ref']==ref)
        if not c['lib_id'].endswith(':74HCT574'): raise ValueError(f'Unexpected register symbol: {ref}')
        mapping[ref]={p['number']:next(n['labels'] for n in nets if [ref,p['number']] in n['nodes']) for p in c['pins']}
        if 'GND' not in mapping[ref]['10'] or not {'+5V','5V'}&set(mapping[ref]['20']):
            raise ValueError(f'Register supply connectivity: {ref}')
    write_json(folder/'pin-map.json',mapping)
    # Generate connections from the extracted pin nets, not the assumed bit order.
    signals={'GND':"1'b0"}
    for bit in range(8): signals[f'D{bit}']=f'data[{bit}]'; signals[f'INSTR{bit}']=f'instruction[{bit}]'
    for i,name in enumerate(refs.values()):
        signals[f'{name}_clock']=f'clocks[{i}]'; signals[f'~{name}_out']=f'oe_n[{i}]'
    def sig(ref,pin):
        candidates={signals[n] for n in mapping[ref][str(pin)] if n in signals}
        if len(candidates)!=1: raise ValueError(f'Unresolved slice pin: {ref}.{pin}')
        return candidates.pop()
    text=['`timescale 1ns/1ps', 'module slice;', 'tri [7:0] data; wire [7:0] instruction;',
          'reg [7:0] stimulus; reg drive=1; reg [5:0] clocks=0, oe_n=63;',
          'integer r,v,checks=0; assign data=drive ? stimulus : 8\'bz;']
    for ref in refs:
        ins=','.join(sig(ref,p) for p in range(9,1,-1))
        outs=','.join(sig(ref,p) for p in range(12,20))
        text.append(f'hct574 {ref} (.d({{{ins}}}),.q({{{outs}}}),.clk({sig(ref,11)}),.oe({sig(ref,1)}));')
    text+=['''initial begin
  $dumpfile("slice.vcd"); $dumpvars(0,slice);
  for(r=0;r<6;r=r+1) begin
    for(v=0;v<256;v=v+1) begin
      // Allow output-disable settling before the first setup interval.
      oe_n=63; drive=1; stimulus=v; #100;
      clocks[r]=1; #60; clocks[r]=0;
      drive=0;
      if(r<5) oe_n[r]=0;
      #60;
      if(r<5 && data !== v[7:0]) $fatal(1,"register %0d value %0d got %h",r,v,data);
      if(r==5 && instruction !== v[7:0]) $fatal(1,"IR value %0d got %h",v,instruction);
      checks=checks+1;
      oe_n=63; #60;
      if(data !== 8'bz) $fatal(1,"bus failed to release");
    end
  end
  $display("DONE checks=%0d",checks); $finish;
end
endmodule
module hct574(input [7:0] d, input clk,oe, output [7:0] q);
  reg [7:0] stored;
  always @(posedge clk) stored <= #45 d;
  assign #50 q=oe ? 8'bz : stored;
endmodule
''']
    (folder/'slice.sv').write_text('\n'.join(text))
    code,log=command(['iverilog','-g2012','-o',folder/'slice.vvp',folder/'slice.sv'])
    if code:
        (folder/'slice.log').write_text(log)
        raise RuntimeError(log)
    code,runlog=command(['vvp',folder/'slice.vvp'],cwd=folder); log+=runlog
    (folder/'slice.log').write_text(log)
    ok=code==0 and 'DONE checks=1536' in log
    return evidence('registers','Schematic-derived register slice','pass' if ok else 'fail',
                    'Six physical register pin maps; 256 values per register plus bus-release checks.',
                    artifacts=['registers/pin-map.json','registers/slice.sv','registers/slice.log','registers/slice.vcd'],
                    limitation='Register-only boundary stimulus; clock decoding, stack pointer, surrounding drivers and power integrity excluded. Behavioural timing, not device qualification.')
