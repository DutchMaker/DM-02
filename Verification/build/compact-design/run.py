"""Reproducible CP1 preparation and bounded pin-derived simulation profiles."""
from pathlib import Path
import argparse,hashlib,json,shutil,struct,sys,time,subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];CANDIDATE=HERE/'candidate'
sys.path.insert(0,str(CANDIDATE/'Verification'))
from dm02.common import VROOT,BUILD,write_json,command,digest
from designs.compact_candidate import generate
from designs.compact_candidate import LEAVES,SOURCE_GROUPS,GROUP_REFS
from dm02.compact_hardware import Circuit,support_hdl
from dm02.sequencer import fixtures
from dm02.instruction_fixtures import generate as opcode_fixtures

def prepare():
    generate();inputs={}
    for name in ['microcode/microcode.rom']+[f'alu/alu{i}.rom' for i in range(8)]:
        src=ROOT/'Verification/build'/name;dest=BUILD/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dest);inputs[name]=digest(src)
    f=BUILD/'compact/fixtures';f.mkdir(parents=True,exist_ok=True)
    coverage=fixtures(f);coverage['opcodes']=opcode_fixtures(f)
    data=(BUILD/'microcode/microcode.rom').read_bytes();words=struct.unpack('<65536H',data)
    (f/'control.hex').write_text(''.join(f'{w:04x}\n' for w in words))
    assert struct.pack('<65536H',*[int(x,16) for x in (f/'control.hex').read_text().split()])==data
    write_json(HERE/'fixture-inputs.json',dict(inputs=inputs,coverage=coverage))

def bench():
    t=(VROOT/'hdl/sequencer_tb.sv').read_text()
    t=t.replace('always #62.5 osc=~osc;',
        'parameter real OSC_DUTY=0.5,OSC_PPM=0;\n'
        'initial forever begin #(250/(1+OSC_PPM/1.0e6)*(1-OSC_DUTY)) osc=1;'
        '#(250/(1+OSC_PPM/1.0e6)*OSC_DUTY) osc=0;end')
    t=t.replace('reg osc=0,reset_n=1,run=0,resume=0,step=0;',
        'reg osc=0,reset_request_n=1,run=0,resume=0,step=0;wire reset_n,init_clk;')
    # The testbench drives only the supervisor-request input. System reset is
    # the physical C1 falling-edge synchronizer, not a testbench delay.
    import re
    t=re.sub(r'\breset_n\s*=', 'reset_request_n=',t)
    t=t.replace('counted_clock source(osc,reset_n,request,step,phase,active,ready,clock_state);',
        'counted_clock source(osc,reset_request_n,request,step,phase,active,ready,clock_state,init_clk,reset_n);')
    t=t.replace('data_bus,stack_address,sp);','data_bus,stack_address,sp,init_clk,phase[2]);')
    t=t.replace('address_bus,stack_address,data_bus,mar);','address_bus,stack_address,data_bus,mar,init_clk,phase[2]);')
    t=t.replace('data_bus,{b,c,h,l});','data_bus,{b,c,h,l},init_clk);')
    # Explicit physical receiver branches; every replacement must match once.
    def replace(old,new):
        nonlocal t
        assert t.count(old)==1,(old,t.count(old));t=t.replace(old,new)
    declarations=[f'wire [{len(LEAVES)-1}:0] distribution_leaves;',
        'compact_distribution tree(phase,init_clk,reset_n,distribution_leaves);',
        'tri [31:0] source_buses;']
    declarations += [f'wire {leaf}=distribution_leaves[{i}];' for i,(root,leaf) in enumerate(LEAVES)]
    declarations += ['wire [3:0] SQ1_phase={SQ1_PH3,SQ1_PH2,SQ1_PH1,SQ1_PH0};']
    replace('wire [7:0] opcode;', '\n'.join(declarations)+'\nwire [7:0] opcode;')
    replace('tri [7:0] data_bus;tri [15:0] address_bus;wire [15:0] pc;',
        'tri [7:0] data_bus;tri [15:0] address_bus;wire [15:0] pc;\n'
        'compact_bus fabric(source_buses,{out_n[14:11],mem_n,out_n[9:1]},data_bus,BF1_RESET_n);')
    replace('control(phase[1],cw_ph2,reset_n,','control(CW1_PH1,cw_ph2,CW1_RESET_n,')
    replace('dut(phase,reset_n,','dut(SQ1_phase,SQ1_RESET_n,')
    replace('counter(phase[3],reset_n,','counter(PC1_PH3,PC1_RESET_n,')
    replace('data_bus,address_bus,pc);','data_bus,address_bus,pc,source_buses[23:16]);')
    replace('memory(phase[0],phase[2],phase[3],reset_n,','memory(ME1_PH0,ME1_PH2,ME1_PH3,ME1_RESET_n,')
    replace('io_address,io_strobe);','io_address,io_strobe,source_buses[31:24]);')
    replace('stack(phase[1],phase[3],reset_n,','stack(SP1_PH1,SP1_PH3,SP1_RESET_n,')
    replace('data_bus,stack_address,sp,init_clk,phase[2]);','data_bus,stack_address,sp,SP1_INIT_CLK,SP1_PH2,source_buses[23:16]);')
    replace('address(phase[1],phase[3],reset_n,','address(MA1_PH1,MA1_PH3,MA1_RESET_n,')
    replace('data_bus,mar,init_clk,phase[2]);','data_bus,mar,MA1_INIT_CLK,MA1_PH2,source_buses[31:24]);')
    replace('alu(phase[1],phase[3],reset_n,','alu(AL1_PH1,AL1_PH3,AL1_RESET_n,')
    replace('data_bus,a,flags,rom_address,result);','data_bus,a,flags,rom_address,result,source_buses[7:0]);')
    replace('registers(phase[3],reset_n,','registers(RG1_PH3,RG1_RESET_n,')
    replace('data_bus,{b,c,h,l},init_clk);','data_bus,{b,c,h,l},RG1_INIT_CLK,source_buses[15:8]);')
    paths={'AL1':'physical_alu.alu','RG1':'physical_registers.registers','PC1':'counter',
           'SP1':'physical_address.stack','MA1':'physical_address.address','ME1':'physical_memory.memory'}
    physical=[paths[name]+'.cp_active_'+ref for name,refs in GROUP_REFS.items() for ref in refs]
    monitors='''
 wire [13:0] physical_sources={%s};
 real last_release=-10000,min_blank=1.0e9;integer handovers=0;
 always @(physical_sources) if(reset_n && monitor) begin
   if($countones(physical_sources)>1) $fatal(1,"CP1 physical source contention");
   if(physical_sources===0) last_release=$realtime;
   else if(!$isunknown(physical_sources) && last_release>0) begin
     if($realtime-last_release<min_blank) min_blank=$realtime-last_release;
     handovers=handovers+1;
   end
 end
 final $display("CP1 physical bus handovers=%%0d minimum_disabled_ns=%%0.3f",handovers,min_blank);
'''%(','.join(physical))
    t=t.replace('\nendmodule',monitors+'\nendmodule')
    # Preserve the functional observation point relative to phase at 4 MHz.
    t=t.replace('#320;','#600;').replace('@(posedge phase[3]);#100;','@(posedge phase[3]);#250;')
    return t

def profile(corner=0,cases=False,demo=None,boot=False,duty=0.5,ppm=0):
    label='boot' if boot else demo or 'cases'+str(int(cases))
    if duty!=0.5 or ppm:label+=f'-d{duty}-ppm{ppm}'
    folder=BUILD/'compact'/f'c{corner}-{label}'
    folder.mkdir(parents=True,exist_ok=True)
    f=BUILD/'compact/fixtures'
    coverage=None
    if boot:
        from dm02.bootloader import fixtures as boot_fixtures
        f=BUILD/'compact/fixtures-boot';coverage=boot_fixtures(f,full_demo=True)
    elif demo:
        from dm02.hardware_programs import fixtures as demo_fixtures
        f=BUILD/'compact'/('fixtures-'+demo);coverage=demo_fixtures(f,demo)
    for name in ('program.hex','alu.bin','expected.txt','instructions.txt','cases.txt','io-expected.txt','boot-rom.hex','sram-power-on.hex','loader-target.hex'):
        if not (f/name).exists():continue
        shutil.copyfile(f/name,folder/name)
    shutil.copyfile(BUILD/'compact/fixtures/control.hex',folder/'control.hex')
    names=['C1','CW1','SQ1','PC1','AL1','RG1','SP1','MA1','ME1','BF1','DT1']
    for name in names:(folder/(name+'.sv')).write_text(Circuit(name).hdl(corner))
    (folder/'support.sv').write_text((VROOT/'hdl/controller_devices.sv').read_text()+support_hdl())
    (folder/'tb.sv').write_text(bench())
    if boot:
        from dm02.boot_hardware import memory_hdl,testbench
        (folder/'ME1.sv').write_text(memory_hdl((folder/'ME1.sv').read_text()))
        text=(folder/'support.sv').read_text();assert text.count('initial $readmemh("program.hex",memory,0,65535);')==1
        (folder/'support.sv').write_text(text.replace('initial $readmemh("program.hex",memory,0,65535);','initial $readmemh("sram-power-on.hex",memory);'))
        (folder/'tb.sv').write_text(testbench((folder/'tb.sv').read_text(),coverage))
    args=['iverilog','-g2012','-s','sequencer_tb','-o','compact.vvp']
    for k,v in dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,CASE_SUITE=int(cases),DEMO=int(bool(demo or boot)),OSC_DUTY=duty,OSC_PPM=ppm).items():args+=['-P',f'sequencer_tb.{k}={v}']
    args += [n+'.sv' for n in names]+['support.sv','tb.sv']
    code,log=command(args,cwd=folder,timeout=120)
    if code:
        (folder/'compile.log').write_text(log);raise RuntimeError(log)
    start=time.monotonic()
    budget=300
    if demo or boot:
        # The full graphics program has >2.2 million microcycles. Derive its
        # execution budget from completed profiles rather than a fixed hour.
        observed=[]
        for source,cycles in [('c1-cases0',1424),('c1-cases1',23002),('c1-hello_world',825)]:
            p=BUILD/'compact'/source/'result.json'
            if p.exists():
                previous=json.loads(p.read_text())
                if previous['passed']:observed.append(previous['wall_seconds']/cycles)
        seconds_per_cycle=max(observed or [0.01])
        import math
        budget=max(3600,math.ceil(coverage['microcycles']*seconds_per_cycle*2.5))
        write_json(folder/'execution-budget.json',dict(timeout_seconds=budget,microcycles=coverage['microcycles'],
            observed_seconds_per_cycle=seconds_per_cycle,headroom_factor=2.5))
    try:code,out=command(['vvp','compact.vvp'],cwd=folder,timeout=budget)
    except subprocess.TimeoutExpired as e:
        code=124;out=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else (e.stdout or '')
        out+='\nTIMEOUT: profile incomplete\n'
    log+=out;(folder/'simulation.log').write_text(log)
    done='DONE hardware-demo' if demo or boot else 'DONE fetched-opcodes' if cases else 'DONE sequencer'
    result=dict(corner=corner,cases=cases,demo=demo,boot=boot,duty=duty,ppm=ppm,passed=code==0 and done in log,
        exit_code=code,timeout_seconds=budget,wall_seconds=time.monotonic()-start,log=str((folder/'simulation.log').relative_to(HERE)))
    result['model_hashes']={p.name:digest(p) for p in sorted(folder.glob('*.sv'))}
    result['schematic_hashes']={n:digest(CANDIDATE/f'Circuits/KiCad/Compact/candidates/{n}.sch') for n in names}
    result['fixture_hashes']={p.name:digest(p) for p in sorted(folder.iterdir()) if p.suffix in ('.hex','.bin') or p.name in ('expected.txt','instructions.txt','cases.txt','io-expected.txt')}
    if coverage:
        from dm02.hardware_programs import render
        result['coverage']=coverage
        if result['passed']:
            result['output']=render(folder,'emulator_demo' if boot else demo)
            result['passed'] &= result['output']['passed'] and result['output']['io_events']==coverage['io_events']
            if boot:
                from dm02.boot_hardware import verify_log
                result['boot_check']=verify_log(log,coverage);result['passed'] &= result['boot_check']['passed']
    write_json(folder/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ('model_hashes','schematic_hashes','coverage')}));print(log[-5000:])
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--corner',type=int,default=0);p.add_argument('--cases',action='store_true');p.add_argument('--demo');p.add_argument('--boot',action='store_true')
    a=p.parse_args()
    if a.prepare:prepare()
    else:profile(a.corner,a.cases,a.demo,a.boot)
