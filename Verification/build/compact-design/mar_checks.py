"""Independent MAR oracle: full wrap, byte loads and every PC/SP snapshot."""
from pathlib import Path
import importlib.util,json
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import BUILD,VROOT,command,write_json,digest
from dm02.compact_hardware import Circuit,support_hdl

TB='''`timescale 1ns/1ps
module mar_tb;
 parameter FULL=1;
 reg init_clk=0,reset_n=0,ph1=0,ph2=0,ph3=0,inc=0,fetch0=0,pct=0,spt=0,ll=1,lh=1;
 reg [15:0] pc_data=0,sp_data=0,expected=0;reg [7:0] value=0;reg host=0;
 wire [7:0] data_bus=host ? value : 8'bz;tri [7:0] source_bus;wire [15:0] address;
 always #125 init_clk=~init_clk;
 memory_address dut(ph1,ph3,reset_n,inc,fetch0,pct,spt,ll,lh,1'b1,1'b1,pc_data,sp_data,data_bus,address,init_clk,ph2,source_bus);
 integer i,checked=0;
 task cycle;
 begin
   @(posedge init_clk);#40;ph1=1;#250;ph1=0;ph2=1;
   #750;ph3=1;#250;
   if(address!==expected) $fatal(1,"CP MAR mismatch row=%0d got=%h want=%h",checked,address,expected);
   checked=checked+1;ph2=0;ll=1;lh=1;fetch0=0;pct=0;spt=0;
   #750;ph3=0;#50;
 end
 endtask
 initial begin
   #1;reset_n=1;#1;reset_n=0;#2000;@(negedge init_clk);#20;reset_n=1;#500;
   if(address!==0) $fatal(1,"CP MAR zero initialization");
   inc=1;
   for(i=1;i<=(FULL?65536:32);i=i+1) begin expected=i&65535;cycle();end
   inc=0;host=1;
   for(i=0;i<256;i=i+1) begin
     value=i;ll=0;expected={address[15:8],value};cycle();
     value=255-i;lh=0;expected={value,address[7:0]};cycle();
   end
   host=0;
   for(i=0;i<65536;i=i+(FULL?1:257)) begin
     pc_data=i;sp_data=~i;pct=1;expected=pc_data;cycle();
     spt=1;expected=sp_data;cycle();
   end
   for(i=0;i<256;i=i+1) begin pc_data=i*257;fetch0=1;expected=pc_data;cycle();end
   $display("DONE CP MAR rows=%0d full=%0d",checked,FULL);$finish;
 end
 initial begin #600000000;$fatal(1,"CP MAR watchdog");end
endmodule
'''

def run(corner=1,full=True,fault=False):
    folder=BUILD/'compact'/f'mar-c{corner}-full{int(full)}-fault{int(fault)}';folder.mkdir(parents=True,exist_ok=True)
    c=Circuit('MA1')
    if fault:c.nodes['U4','14']=c.labels['5V']
    (folder/'mar.sv').write_text(c.hdl(corner));(folder/'clock.sv').write_text(Circuit('C1').hdl(corner))
    (folder/'support.sv').write_text((VROOT/'hdl/controller_devices.sv').read_text()+support_hdl());(folder/'tb.sv').write_text(TB)
    code,log=command(['iverilog','-g2012','-s','mar_tb','-P',f'mar_tb.FULL={int(full)}','-o','mar.vvp','mar.sv','clock.sv','support.sv','tb.sv'],cwd=folder);assert code==0,log
    code,out=command(['vvp','mar.vvp'],cwd=folder,timeout=1800);log+=out;(folder/'simulation.log').write_text(log)
    result=dict(corner=corner,full=full,fault=fault,passed=code!=0 and 'CP MAR mismatch' in log if fault else code==0 and 'DONE CP MAR' in log,
        log=str((folder/'simulation.log').relative_to(HERE)),model_hashes={p.name:digest(p) for p in folder.glob('*.sv')})
    write_json(folder/'result.json',result);print(log,flush=True);return result

if __name__=='__main__':
    import sys,hashlib
    results=[]
    for corner,full,fault in [(1,True,False),(4,False,False),(1,False,True)]:
        if '--fault-only' in sys.argv and not fault:
            folder=BUILD/'compact'/f'mar-c{corner}-full{int(full)}-fault0';x=json.loads((folder/'result.json').read_text());assert x['passed']
            assert hashlib.sha256(Circuit('MA1').hdl(corner).encode()).hexdigest()==x['model_hashes']['mar.sv']
            assert hashlib.sha256(TB.encode()).hexdigest()==x['model_hashes']['tb.sv']
        else:x=run(corner,full,fault)
        results.append(x)
        write_json(HERE/'mar-check.json',dict(passed=all(x['passed'] for x in results),complete=len(results)==3,runs=results));assert x['passed']
