"""Serial CP1 regression; stop on failure and retain every run's evidence."""
from pathlib import Path
import importlib.util,json,struct,time
HERE=Path(__file__).resolve().parent
def module(name):
    s=importlib.util.spec_from_file_location('cp_'+name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=module('run');counters=module('counters');registers=module('registers');faults=module('faults');modules=module('module_checks');mar=module('mar_checks')
from dm02.common import ROOT,VROOT,BUILD,write_json,command,digest
from dm02.compact_hardware import Circuit
from dm02.alu import expected
from dm02.microcode import reference

def roms():
    raw=b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8));assert len(raw)==4194304
    words=struct.unpack('<2097152H',raw)
    for a,w in enumerate(words):assert w==expected(a>>16,(a>>8)&255,a&255),(a,w)
    spec=reference((ROOT/'Code/Microcode/microcode.src').read_text())
    control=(BUILD/'microcode/microcode.rom').read_bytes();assert control==struct.pack('<65536H',*spec['words'])
    for a,w in enumerate(spec['words']):
        fs=[(w>>1)&15] if w&0x8000 and not w&64 else [] if w&0x8000 else [(w>>11)&15,(w>>1)&15]
        load=(w>>7)&15 if w&0x8000 else 0
        assert not(load in (13,14) and any(x in fs for x in (3,4)))
        assert not(load in (8,9) and 8 in fs)
    folder=HERE/'programming-images';folder.mkdir(exist_ok=True)
    (folder/'M27C322-little-endian.bin').write_bytes(raw)
    (folder/'M27C1024-little-endian.bin').write_bytes(control)
    result=dict(passed=True,alu_addresses=len(words),control_words=len(spec['words']),counter_conflicting_words=0,
        images={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in folder.glob('*.bin')},
        physical_programming_readback=False,word_format='16-bit word address order, low byte first; programmer adapter/byte convention must be checked against readback.')
    write_json(HERE/'rom-check.json',result);return result

def clocks():
    results=[]
    for corner in range(10):
        folder=BUILD/'compact'/f'clock-c{corner}';folder.mkdir(parents=True,exist_ok=True)
        (folder/'clock.sv').write_text('`define DM02_OSC_PERIOD_NS 250\n'+Circuit('C1').hdl(corner))
        pilot=json.loads((VROOT/'requirements.json').read_text())['pilot']
        (folder/'parameters.vh').write_text('\n'.join(f'`define {k.upper()} {v}' for k,v in pilot.items())+'\n')
        tb=(VROOT/'hdl/clock_candidate_tb.sv').read_text().replace('phase,active,ready,state);','phase,active,ready,state,,);')
        (folder/'tb.sv').write_text(tb)
        code,log=command(['iverilog','-g2012','-s','clock_candidate_tb','-o','clock.vvp','clock.sv','tb.sv'],cwd=folder);assert code==0,log
        for duty in (0.37,0.45,0.5,0.55,0.63):
            for ppm in (-30,0,30):
                code,log=command(['vvp','clock.vvp',f'+DUTY={duty}',f'+PPM={ppm}'],cwd=folder)
                p=folder/f'd{duty}-ppm{ppm}.log';p.write_text(log)
                passed=code==0 and 'DONE counted-clock' in log
                results.append(dict(corner=corner,duty=duty,ppm=ppm,passed=passed,log=str(p.relative_to(HERE))))
                assert passed,log
    write_json(HERE/'clock-check.json',dict(passed=all(x['passed'] for x in results),runs=results));return results

def main():
    start=time.time();results=[]
    write_json(HERE/'verification-state.json',dict(state='running',started_at=start))
    try:
        roms();clocks()
        for corner in (0,1,4):
            x=counters.run(corner,True);results.append(x);assert x['passed']
        x=counters.run(1,False,True);results.append(x);assert x['passed']
        register_runs=[registers.run(c) for c in (0,1,5)]+[registers.run(1,f) for f in ('enable','init-clock')]
        write_json(HERE/'register-check.json',dict(passed=all(x['passed'] for x in register_runs),runs=register_runs));assert all(x['passed'] for x in register_runs)
        module_runs=[]
        for board,corner,quick in [('AL1',1,False),('ME1',1,False),('AL1',4,True),('ME1',4,True)]:
            x=modules.run(board,corner,quick);module_runs.append(x);assert x['passed']
        write_json(HERE/'module-check.json',dict(passed=True,complete=True,runs=module_runs))
        mar_runs=[]
        for corner,full,fault in [(1,True,False),(4,False,False),(1,False,True)]:
            x=mar.run(corner,full,fault);mar_runs.append(x);assert x['passed']
        write_json(HERE/'mar-check.json',dict(passed=True,complete=True,runs=mar_runs))
        for corner in range(12):
            x=r.profile(corner);results.append(x);assert x['passed']
        for corner in (1,4,7):
            for duty in (0.37,0.63):
                for ppm in (-30,30):
                    x=r.profile(corner,duty=duty,ppm=ppm);results.append(x);assert x['passed']
        fault_runs=faults.device_faults()+[faults.bus_fault()]
        write_json(HERE/'fault-check.json',dict(passed=all(x['detected'] for x in fault_runs),results=fault_runs));assert all(x['detected'] for x in fault_runs)
        for corner in (0,1,7):
            x=r.profile(corner,True);results.append(x);assert x['passed']
        for demo,boot in [('hello_world',False),(None,True)]:
            x=r.profile(1,demo=demo,boot=boot);results.append(x);assert x['passed']
    except Exception as e:
        write_json(HERE/'verification-state.json',dict(state='failed',started_at=start,finished_at=time.time(),error=repr(e),runs=results));raise
    write_json(HERE/'verification-state.json',dict(state='complete',passed=True,started_at=start,finished_at=time.time(),runs=results))
    print('CP1 serial regression complete',flush=True)
if __name__=='__main__':main()
