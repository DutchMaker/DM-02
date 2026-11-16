"""Bounded new ROM/text startup matrix; reuse the completed maximum baseline."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02 import text_boot
from dm02.common import digest,write_json


def main():
    assert not (HERE/'matrix.json').exists(),'Preserve TB1 matrix'
    baseline=json.loads((HERE/'guarded-max/result.json').read_text())
    assert baseline['passed'] and all(digest(ROOT/n)==h for n,h in baseline['source_hashes'].items())
    cases=[('seed-0',dict(seed=0)),('seed-255',dict(seed=255)),
        ('zero',dict(corner=0,bridge_profile=0,text_profile=0,seed=0x5a)),
        ('mixed2',dict(corner=2,bridge_profile=2,text_profile=2)),
        ('mixed3',dict(corner=3,bridge_profile=3,text_profile=3))]
    cases += [('fault-'+f,dict(fault=f)) for f in ('wrong-loader-byte','wrong-loader-address','skip-loader')]
    def run(item):
        name,kwargs=item;return name,text_boot.run(HERE/name,**kwargs)
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(run,cases))
    results={'guarded-max':baseline,**results}
    write_json(HERE/'matrix.json',dict(revision='CP1-TB1',accepted_revision='CP1-R2',results=results,
        script_sha256=digest(__file__),physical_qualification=False,rom_only_startup=True,host_boot_injected=False))
    assert all(r['passed']==(r['fault'] is None) for r in results.values()),'Unexpected TB1 result'
    print('PASS TB1 matrix: six ROM-startup profiles and three detected loader faults')


if __name__=='__main__':main()
