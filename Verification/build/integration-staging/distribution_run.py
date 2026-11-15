"""Explicit FD1 simulation assembly; no process-global factory substitution."""
import json
import shutil
import subprocess
from pathlib import Path
from dm02.common import ROOT,VROOT,BUILD,command,digest,write_json
from dm02.controller_hardware import roms
from dm02.alu_hardware import fixtures
from dm02.instruction_fixtures import generate as opcode_fixtures
from dm02.hardware_programs import fixtures as demo_fixtures,render
from distribution_candidate import generate
from distribution_hardware import load_boards,exported_hdl,ClockTree,ResetTree,Fabric,Selector,PARTS
from distribution_bench import bench


def profile(circuits,folder,fixture,corner=1,tree_corner=1,fabric_corner=1,cases=False,demo=False):
    if cases and demo:raise ValueError('A profile cannot be both opcode suite and demo')
    circuits=Path(circuits).resolve();folder=Path(folder).resolve();fixture=Path(fixture).resolve()
    required=['alu.bin','program.hex','expected.txt']
    if cases:required.extend(['cases.txt','instructions.txt'])
    if demo:required.append('io-expected.txt')
    missing=[name for name in required if not (fixture/name).is_file()]
    if missing:raise ValueError('Missing FD1 fixtures: '+', '.join(missing))
    folder.mkdir(parents=True,exist_ok=True);boards=load_boards(circuits)
    inputs=[*circuits.glob('*.sch'),PARTS,*[Path(__file__).with_name(name) for name in
            ('distribution_candidate.py','distribution_hardware.py','distribution_bench.py','distribution_run.py')]]
    inputs += [p for p in fixture.iterdir() if p.is_file()]
    hashes={str(p.relative_to(ROOT)):digest(p) for p in inputs}
    for name in ('alu.bin','vectors.hex','program.hex','expected.txt','cases.txt','instructions.txt','io-expected.txt'):
        source=fixture/name
        if source.exists():shutil.copyfile(source,folder/name)
    boards['AL1'].prepare_simulation(folder);roms(folder)
    names={'AL1':'alu','C1':'clock','CW1':'controller','PC1':'pc','SQ1':'sequencer','RG1':'registers','ME1':'memory'}
    texts={file+'.sv':exported_hdl(boards[name],corner,name) for name,file in names.items()}
    texts['address.sv']=exported_hdl(boards['SP1'],corner,'SP1')+'\n'+exported_hdl(boards['MA1'],corner,'MA1')
    for name,cls,path,c in [('clock-tree',ClockTree,'Clock-Distribution.sch',tree_corner),
                          ('reset-tree',ResetTree,'Reset-Distribution.sch',tree_corner),
                          ('data-fabric',Fabric,'Data-Fabric.sch',fabric_corner),
                          ('data-selector',Selector,'Data-Selector.sch',fabric_corner)]:texts[name+'.sv']=cls(circuits/path).hdl(c)
    texts['sequencer_tb.sv']=bench()
    for name,text in texts.items():(folder/name).write_text(text)
    parameters=dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,CASE_SUITE=int(cases),DEMO=int(demo),
                    STARTUP_WAIT_NS=boards['AL1'].power_on_wait_ns)
    args=['iverilog','-g2012','-s','sequencer_tb']
    for name,value in parameters.items():args.extend(['-P',f'sequencer_tb.{name}={value}'])
    args += ['-o','alu.vvp',*texts]
    code,log=command(args,cwd=folder)
    (folder/'compile.log').write_text(log)
    if code:raise RuntimeError('FD1 compile: '+log)
    timeout=7200 if demo else 180
    try:code,out=command(['vvp','alu.vvp'],cwd=folder,timeout=timeout)
    except subprocess.TimeoutExpired as err:
        out=err.stdout or '';out=out.decode('utf-8',errors='replace') if isinstance(out,bytes) else out
        (folder/'alu.log').write_text(log+out+f'\nFD1 simulation timed out after {timeout} seconds.\n');raise
    log+=out;(folder/'alu.log').write_text(log)
    done='DONE hardware-demo' if demo else 'DONE fetched-opcodes' if cases else 'DONE sequencer'
    stable=all(digest(ROOT/path)==want for path,want in hashes.items())
    result=dict(passed=code==0 and done in log and stable,corner=corner,tree_corner=tree_corner,fabric_corner=fabric_corner,
                cases=cases,demo=demo,folder=str(folder.relative_to(ROOT)),log=log,input_hashes=hashes,inputs_stable=stable,
                generated_hdl_hashes={name:digest(folder/name) for name in texts},parameters=parameters,
                simulation_timeout_seconds=timeout,topology='AL2/CD1/RD1/DF2 at 4 MHz; AL1 is the AL2 connector slot')
    write_json(folder/'profile.json',result);return result


def main():
    folder=BUILD/'integration-staging';circuits=folder/'circuits';generate(circuits)
    fixture=folder/'fixtures';fixtures(fixture);opcode_fixtures(fixture)
    results=[]
    for logic,tree,fabric in [(0,0,0),(0,1,1),(1,0,0),(1,1,1),(1,2,2),(2,3,3),(3,4,4),(4,5,5)]:
        r=profile(circuits,folder/f'continuous-{logic}-{tree}-{fabric}',fixture,logic,tree,fabric)
        assert r['passed'],r;results.append(r);print('Clean FD1 continuous',logic,tree,fabric,'pass',flush=True)
    write_json(folder/'continuous.json',results);results=[]
    for corner in (0,1,2):
        r=profile(circuits,folder/f'opcodes-{corner}',fixture,corner,corner,corner,cases=True)
        assert r['passed'],r;results.append(r);print('Clean FD1 all-opcode',corner,'pass',flush=True)
    write_json(folder/'opcodes.json',results)
    fixture=folder/'hello-fixture';coverage=demo_fixtures(fixture,'hello_world')
    r=profile(circuits,folder/'hello',fixture,demo=True);assert r['passed'],r
    output=render(folder/'hello','hello_world');assert output['passed'] and output['io_events']==coverage['io_events']
    write_json(folder/'hello.json',dict(simulation=r,output=output,coverage=coverage))
    print('Clean FD1 exact hello pass; eight continuous and three opcode profiles complete',flush=True)


if __name__=='__main__':main()
