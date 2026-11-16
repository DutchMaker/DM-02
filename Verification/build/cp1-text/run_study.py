"""Run once into a new matrix directory; retain development and negative evidence."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import text_card,text_cpu
from dm02.common import digest,write_json


def main():
    target=HERE/'final'
    if target.exists():raise ValueError('Preserve final matrix; choose a new study directory')
    target.mkdir()
    circuit=text_card.Circuit(HERE/'iteration-2/native/TX1')
    audit=circuit.audit();assert not audit['over_screen']
    write_json(target/'audit.json',audit)
    standalone=[(f'logic-{p}',p,0,None) for p in range(4)]
    standalone += [(f'ppm-{ppm}',1,ppm,None) for ppm in (-30,30)]
    standalone += [(f'fault-{name}',1,0,name) for name in ('mailbox-overwrite','early-credit','reversed-bits','stale-read-address')]
    def one(item):
        name,profile,ppm,fault=item
        c=circuit.fault(fault) if fault else circuit
        result=text_card.simulate(c,target/name,profile,ppm)
        return name,dict(result,fault=fault)
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(one,standalone))
    cpus=[('cpu-max',{}),('cpu-zero',dict(corner=0,bridge_profile=0,text_profile=0)),
          ('cpu-mixed2',dict(corner=2,bridge_profile=2,text_profile=2)),
          ('cpu-mixed3',dict(corner=3,bridge_profile=3,text_profile=3)),
          ('cpu-fast',dict(ppm=30)),('cpu-absent',dict(absent=True))]
    def cpu(item):
        name,kwargs=item
        return name,text_cpu.run(circuit,target/name,**kwargs)
    with ThreadPoolExecutor(max_workers=3) as pool:cpu_results=dict(pool.map(cpu,cpus))
    write_json(target/'matrix.json',dict(revision='CP1-TX1',standalone=results,cpu=cpu_results,
        script_sha256=digest(__file__),physical_qualification=False,accepted_revision='CP1-R2',
        autonomous_rom_boot=False,native_folder='iteration-2/native/TX1'))
    assert all(r['passed']==(r['fault'] is None) for r in results.values()),'Unexpected standalone outcome'
    assert all(r['passed'] for r in cpu_results.values()),'CPU integration failure'
    print('PASS TX1 matrix: six serial profiles, four detected faults, six CPU profiles')


if __name__=='__main__':main()
