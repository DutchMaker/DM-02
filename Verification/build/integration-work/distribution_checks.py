"""FD1 wiring mutations and qualification of seven local receiver guards."""
import shutil
from pathlib import Path
from designs.distribution_candidate import RECEIVERS,relabel
from .common import command,write_json
from .distribution_bench import bench
from .distribution_links import all_boards
from .distribution_run import profile


def wiring_faults(circuits,folder,fixture):
    results=[]
    faults=[('AL1','U13',18,'DF_SOURCE1_1'),('PC1','U5',18,'DF_SOURCE12_1'),
            ('RG1','U7',18,'DF_SOURCE2_1'),('SP1','U20',18,'DF_SOURCE14_1'),
            ('MA1','U40',18,'DF_SOURCE9_1'),('ME1','U9',18,'DF_SOURCE10_1'),
            ('CW1','U901',2,'WORD12'),('SEL','U2',1,'GND'),('DF1','J24',3,'RG1_DATA1')]
    boards=all_boards(circuits)
    for index,(name,ref,pin,label) in enumerate(faults):
        dest=folder/f'wiring-{index}';copies=dest/'circuits';copies.mkdir(parents=True,exist_ok=True)
        for source in Path(circuits).glob('*.sch'):shutil.copyfile(source,copies/source.name)
        circuit=boards[name];path=copies/Path(circuit.sheet['source']).name
        path.write_text(relabel(path.read_text(),circuit.sheet,[(ref,pin,label)]))
        result=profile(copies,dest/'simulation',fixture,0,0,0,cases=True)
        detected=not result['passed'] and 'FATAL:' in result['log'] and 'watchdog' not in result['log']
        results.append(dict(board=name,ref=ref,pin=pin,label=label,detected=detected,simulation=result))
    write_json(folder/'wiring.json',results);return results


def receiver_guards(folder):
    guard='module df_receiver_guard'+bench().split('module df_receiver_guard',1)[1];results=[]
    for board in RECEIVERS:
        setup=60 if board in ('PC1','SQ1','ME1') else 40;hold=25 if board=='SQ1' else 40
        for fault in ('none','setup','hold','unknown'):
            dest=folder/f'guard-{board}-{fault}';dest.mkdir(parents=True,exist_ok=True)
            su=setup-1 if fault=='setup' else setup+1;hd=hold-1 if fault=='hold' else hold+1
            value="8'bx" if fault=='unknown' else "8'h55"
            top=f'''`timescale 1ns/1ps
module guard_tb;
 reg clock=0,reset_n=0,enable=1;reg [7:0] data=0;
 df_receiver_guard #({setup},{hold}) dut(clock,reset_n,enable,data);
 initial begin #1;reset_n=1;#{99-su};data={value};#{su};clock=1;#{hd};data=8'haa;
 #1;$display("DONE guard fixture");$finish;end
endmodule
'''
            (dest/'guard.sv').write_text(top+guard)
            code,log=command(['iverilog','-g2012','-s','guard_tb','-o','guard.vvp','guard.sv'],cwd=dest)
            if code:raise RuntimeError('FD1 guard compilation: '+log)
            code,log=command(['vvp','guard.vvp'],cwd=dest);(dest/'result.log').write_text(log)
            want={'setup':'DF2 receiver setup','hold':'DF2 receiver hold','unknown':'DF2 unknown receiver data'}.get(fault,'DONE guard fixture')
            ok=want in log and ((code==0)==(fault=='none'))
            results.append(dict(board=board,fault=fault,setup_contract_ns=setup,hold_contract_ns=hold,
                                measured_setup_ns=su,measured_hold_ns=hd,diagnostic=want,passed=ok,log=log))
    write_json(folder/'guards.json',results);return results
