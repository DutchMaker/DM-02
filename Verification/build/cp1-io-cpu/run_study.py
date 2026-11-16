"""Bounded composition matrix; record failures without changing accepted R2/BR1."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import io_cpu
from dm02.common import write_json,digest


def main():
    cases=[(f'cpu-{c}',dict(corner=c)) for c in range(12)]
    cases += [(f'bridge-{p}',dict(bridge_profile=p)) for p in (0,2,3)]
    cases += [(f'absent-{p}',dict(present=p)) for p in (1,2,4,8,15)]
    cases += [(f'endpoint-{n}',dict(endpoint_ns=n)) for n in (0,80,120,160,200,400)]
    cases += [('slow-400',dict(endpoint_ns=400,period_ns=500))]
    cases += [(f'duty-{d}-ppm-{p}',dict(duty=d,ppm=p)) for d,p in ((.37,-30),(.37,30),(.63,-30),(.63,30))]
    cases += [(f'fault-{f}',dict(fault=f)) for f in ('disconnected-return','stale-read-address','return-slot-alias')]
    require_new=HERE/'profiles'
    if require_new.exists():raise ValueError('Preserve the study; choose a separate copy/directory')
    source_hash=digest(__file__)
    def run(item):
        name,kwargs=item
        return name,io_cpu.profile(HERE/'profiles'/name,**kwargs)
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,cases))
    write_json(HERE/'matrix.json',dict(revision='CP1-BI1',baseline_revision='CP1-R2',bridge_revision='CP1-BR1',
        results=results,study_script_sha256=source_hash,physical_qualification=False,
        promoted_into_R2=False,autonomous_rom_boot=False,endpoint_implementation='behavioral qualification fixtures',
        scope='Fetched diagnostic in preloaded ROM/RAM models; conditional sampled integration, not full timing qualification.'))
    print('Matrix:',sum(r['passed'] for r in results.values()),'/',len(results),'passed')


if __name__=='__main__':main()
