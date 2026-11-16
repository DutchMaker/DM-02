"""Stage CP1-R2 from the accepted active source lock, without changing CP1."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.cp1 import materialize,verify_hashes,TARGET


def main():
    candidate=HERE/'candidate'
    if candidate.exists():
        raise RuntimeError('Candidate already exists; preserve completed work')
    lock=json.loads((TARGET/'lock.json').read_text())
    verify_hashes(ROOT/'Verification/build',lock['artifacts'])
    materialize(lock,candidate)
    previous=HERE.parent/'compact-design'
    for name in ('run.py','verify.py','counters.py','registers.py','faults.py','module_checks.py',
                 'mar_checks.py','audit.py','physical.py','component_review.py','interconnect.py','workbook.py'):
        shutil.copyfile(previous/name,HERE/name)
    shutil.copytree(previous/'sources',HERE/'sources')
    for name in ('cd74hct273.pdf','cd74hct273.txt'):
        shutil.copyfile(HERE.parent/'cp1-timing-review'/name,HERE/'sources'/name)
    (HERE/'parent-lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    (HERE/'decision.json').write_text(json.dumps(dict(
        goal='Adopt CD74HCT273E for the three 273 registers and remove the ambiguous clock-delay source.',
        parent='cp1-promotion-2026-11-16',revision='CP1-R2',
        route='Isolated complete source set; explicit part identity; conservative 42 ns delay envelope plus a 3 ns hold monitor; full digital rerun before promotion.',
        evidence='SCHS174D explicitly specifies 38 ns clock-to-Q and 40 ns clear-to-Q at 4.5 V, -40..85 C and 50 pF. Eight earlier sampled profiles passed the additional hold requirement.',
        physical_boundary='No claim about unqualified loads, supply edges, minimum silicon delays, or full physical operating envelope.',
        jev='Installed guidance unavailable; no advisory result claimed.'),indent=2)+'\n')
    print('Prepared',len(lock['sources']),'CP1 inputs')


if __name__=='__main__':main()
