"""Isolated frequency sensitivity of pinned CP1-R2 HDL; never a release gate.

Reuse checked HDL bytes and fixtures. Only the oscillator period and functional
observation timing change; device timing monitors stay unchanged.
Every result, including high-frequency failures, is retained.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ARCHIVE=HERE.parent/'cp1-hct273'
BUILD=ARCHIVE/'candidate/Verification/build/compact'
NAMES=['C1','CW1','SQ1','PC1','AL1','RG1','SP1','MA1','ME1','BF1','DT1','support','tb']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')

def profile(mhz,corner,duty,cases=False,ppm=30,observation='proportional'):
    label=f'f{mhz:g}-c{corner}-d{duty:g}-cases{int(cases)}-ppm{ppm}'
    folder=HERE/('sweep' if observation=='proportional' else 'sweep-capture')/label
    if folder.exists():raise RuntimeError('Preserve existing experiment: '+str(folder))
    source=BUILD/f'c{corner}-cases{int(cases)}'
    receipt=json.loads((source/'result.json').read_text())
    assert receipt['passed']
    lock=json.loads((ROOT/'Verification/targets/cp1/lock.json').read_text())
    assert lock['revision']=='CP1-R2'
    assert lock['artifacts'][str((source/'result.json').relative_to(HERE.parent))]==sha(source/'result.json')
    inputs={}
    for name,h in {**receipt['model_hashes'],**receipt['fixture_hashes']}.items():
        path=source/name
        assert sha(path)==h,name
        key=str(path.relative_to(HERE.parent))
        assert lock['artifacts'].get(key)==h,('not pinned',key)
        inputs[key]=h
    folder.mkdir(parents=True)
    for key in inputs:shutil.copyfile(HERE.parent/key,folder/Path(key).name)
    period=1000/mhz
    bench=(folder/'tb.sv').read_text()
    old='parameter real OSC_DUTY=0.5,OSC_PPM=0;'
    assert bench.count(old)==1
    bench=bench.replace(old,'parameter real OSC_DUTY=0.5,OSC_PPM=0,OSC_PERIOD_NS=250;')
    assert bench.count('250/(1+OSC_PPM/1.0e6)')==2
    bench=bench.replace('250/(1+OSC_PPM/1.0e6)','OSC_PERIOD_NS/(1+OSC_PPM/1.0e6)')
    assert bench.count('#600;')==1 and bench.count('@(posedge phase[3]);#250;')==1
    if observation=='proportional':
        bench=bench.replace('#600;','#(2.4*OSC_PERIOD_NS/(1+OSC_PPM/1.0e6));')
        bench=bench.replace('@(posedge phase[3]);#250;','@(posedge phase[3]);#(OSC_PERIOD_NS/(1+OSC_PPM/1.0e6));')
    else:
        # Observe at the existing connector setup-monitor edge. All timing
        # assertions still apply. Keep the archived 250 ns state-settle window:
        # counter ripple delay does not scale with oscillator frequency.
        bench=bench.replace('#600;','@(posedge phase[3]);')
        bench=bench.replace('@(posedge phase[3]);#250;','#250;')
    # Measurement only: original connector/device assertions are untouched.
    monitor='''
 real min_fetch_setup=1.0e9,min_write_setup=1.0e9;
 integer fetch_samples=0,write_samples=0;
 always @(posedge phase[3]) if(reset_n && monitor) begin
   if(fetch1) begin
     fetch_samples=fetch_samples+1;
     if($realtime-last_data_change<min_fetch_setup) min_fetch_setup=$realtime-last_data_change;
   end
   if(valid && !load_n[10]) begin
     write_samples=write_samples+1;
     if($realtime-last_data_change<min_write_setup) min_write_setup=$realtime-last_data_change;
   end
 end
 final $display("SPEED observed fetch_events=%0d fetch_setup_ns=%0.3f write_events=%0d write_setup_ns=%0.3f",fetch_samples,min_fetch_setup,write_samples,min_write_setup);
'''
    assert bench.count('\nendmodule')==1
    (folder/'tb.sv').write_text(bench.replace('\nendmodule',monitor+'\nendmodule'))
    params=dict(HARD_ALU=1,HARD_REGISTERS=1,HARD_ADDRESS=1,HARD_MEMORY=1,CASE_SUITE=int(cases),DEMO=0,
                OSC_DUTY=duty,OSC_PPM=ppm,OSC_PERIOD_NS=period)
    args=['iverilog','-g2012','-s','sequencer_tb','-o','simulation.vvp']
    for k,v in params.items():args+=['-P',f'sequencer_tb.{k}={v}']
    args += [name+'.sv' for name in NAMES]
    compile_result=subprocess.run(args,cwd=folder,text=True,capture_output=True,timeout=120)
    (folder/'compile.log').write_text(compile_result.stdout+compile_result.stderr)
    assert compile_result.returncode==0,compile_result.stderr
    start=time.monotonic()
    try:
        p=subprocess.run(['vvp','simulation.vvp'],cwd=folder,text=True,capture_output=True,timeout=300)
        log=p.stdout+p.stderr;code=p.returncode
    except subprocess.TimeoutExpired as e:
        log=(e.stdout or b'').decode() if isinstance(e.stdout,bytes) else e.stdout or ''
        log+='\nEXECUTION TIMEOUT: study incomplete\n';code=124
    (folder/'simulation.log').write_text(log)
    done='DONE fetched-opcodes cases=454 cycles=23002' if cases else 'DONE sequencer cycles=1424 halts=3 stepped=12'
    failures=[line for line in log.splitlines() if 'FATAL:' in line]
    result=dict(label=label,oscillator_mhz=mhz,microcycle_hz=mhz*1e6/8,corner=corner,duty=duty,ppm=ppm,
                cases=cases,observation=observation,passed=code==0 and done in log,exit_code=code,wall_seconds=time.monotonic()-start,
                failures=failures,observations=[line for line in log.splitlines() if line.startswith(('SPEED ','CP273 hold','CP1 physical'))],
                input_hashes=inputs,parameters=params,command=args,
                output_hashes={p.name:sha(p) for p in folder.iterdir() if p.is_file() and p.suffix!='.vvp'},
                scope='Sampled digital sensitivity only. Ideal oscillator, allocated loads and fixed selected-device bounds; no physical qualification.')
    write(folder/'result.json',result)
    print(label,'PASS' if result['passed'] else failures or 'INCOMPLETE',flush=True)
    if code==124:raise RuntimeError('Timeout is not a design-failure result')
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mhz',type=float);parser.add_argument('--corner',type=int,default=1)
    parser.add_argument('--duty',type=float,default=.5);parser.add_argument('--cases',action='store_true');parser.add_argument('--ppm',type=int,default=30)
    parser.add_argument('--observation',choices=('proportional','capture'),default='proportional')
    parser.add_argument('--matrix',choices=('proportional','capture'),default='proportional')
    args=parser.parse_args()
    if args.mhz is not None:
        profile(args.mhz,args.corner,args.duty,args.cases,args.ppm,args.observation);return
    output=HERE/('frequency-results.json' if args.matrix=='proportional' else 'capture-results.json')
    assert not output.exists(),'Preserve completed study'
    runs=[profile(4,1,.5,False,0,args.matrix)]
    assert runs[0]['passed'],'Reference profile must pass before changing frequency'
    for mhz in (5,6,8):
        for corner in ((0,1,4,7) if args.matrix=='proportional' else (1,4,7)):
            for duty in (.37,.5,.63):runs.append(profile(mhz,corner,duty,observation=args.matrix))
    write(output,dict(completed=True,physical_qualification=False,runs=runs))
    print('Completed',len(runs),'profiles',flush=True)

if __name__=='__main__':main()
