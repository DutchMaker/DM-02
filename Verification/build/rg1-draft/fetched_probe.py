"""Stage RG1 fetched integration under build/ while the published sources run."""
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from dm02.common import BUILD,VROOT,command,write_json
from dm02.alu_hardware import Circuit as Alu,fixtures
from dm02.pc_hardware import Circuit as Pc
from dm02.controller_hardware import Circuit as Word,roms
from dm02.sequencer import Circuit as Seq
from dm02.clock import Clock
from dm02.instruction_fixtures import generate
import shutil

root=BUILD/'rg1-draft'
spec=importlib.util.spec_from_file_location('dm02.rg1_draft',root/'register_hardware.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.SOURCE=root/'General-Registers.sch'
registers=module.Circuit()
text=(VROOT/'hdl/sequencer_tb.sv').read_text()
replacements=[
 ('parameter HARD_ALU=0,CASE_SUITE=0;', 'parameter HARD_ALU=0,CASE_SUITE=0,HARD_REGISTERS=0;'),
 ('host_a=0,b=0,c=0,h=0,l=0;wire [7:0] a;', 'host_a=0,host_b=0,host_c=0,host_h=0,host_l=0;wire [7:0] a,b,c,h,l;'),
 ('host_a=0;b=0;c=0;h=0;l=0;', 'host_a=0;host_b=0;host_c=0;host_h=0;host_l=0;'),
 ('reg [7:0] peripheral_data;', '''generate if(HARD_REGISTERS) begin : physical_registers
   general_registers registers(phase[3],reset_n,{load_n[5],load_n[4],load_n[3],load_n[2]},
     {out_n[5],out_n[4],out_n[3],out_n[2]},data_bus,{b,c,h,l});
 end else begin : behavioral_registers
   assign b=host_b;assign c=host_c;assign h=host_h;assign l=host_l;
 end endgenerate
 reg [7:0] peripheral_data;''')]
for reg,index in zip('bchl',range(2,6)):
    replacements.extend([(f'peripheral_data={reg};peripheral_drive=1;',f'peripheral_data={reg};peripheral_drive=!HARD_REGISTERS;'),
                         (f'if(!load_n[{index}]) {reg}<=',f'if(!load_n[{index}]) host_{reg}<=')])
for old,new in replacements:
    if text.count(old)!=1:raise ValueError('Unexpected bench anchor '+old)
    text=text.replace(old,new)
(root/'sequencer_tb.sv').write_text(text)
fixtures(root/'fixtures');coverage=generate(root/'fixtures');print(coverage,flush=True)
def profile(config):
    corner,cases=config;folder=root/f'fetched{corner}-cases{int(cases)}';folder.mkdir(exist_ok=True)
    for name in ('alu.bin','vectors.hex','program.hex','expected.txt','cases.txt','instructions.txt'):shutil.copyfile(root/'fixtures'/name,folder/name)
    roms(folder)
    for name,c in [('alu',Alu()),('clock',Clock()),('pc',Pc()),('controller',Word()),('sequencer',Seq()),('registers',registers)]:
        (folder/(name+'.sv')).write_text(c.hdl(corner))
    code,log=command(['iverilog','-g2012','-s','sequencer_tb','-P','sequencer_tb.HARD_ALU=1','-P','sequencer_tb.HARD_REGISTERS=1',
                      '-P',f'sequencer_tb.CASE_SUITE={int(cases)}','-o','fetched.vvp','alu.sv','clock.sv','pc.sv','controller.sv','sequencer.sv','registers.sv',root/'sequencer_tb.sv'],cwd=folder)
    if code:raise RuntimeError(log)
    code,out=command(['vvp','fetched.vvp'],cwd=folder,timeout=180);log+=out;(folder/'fetched.log').write_text(log)
    result=dict(corner=corner,cases=cases,passed=code==0 and ('DONE fetched-opcodes' if cases else 'DONE sequencer') in log,log=log)
    print(result,flush=True);return result
with ThreadPoolExecutor(max_workers=3) as pool:runs=list(pool.map(profile,[(c,False) for c in range(6)]+[(c,True) for c in (0,1,2)]))
write_json(root/'fetched-summary.json',dict(runs=runs,coverage=coverage))
if not all(r['passed'] for r in runs):raise SystemExit(1)
