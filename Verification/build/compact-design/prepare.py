"""Create an isolated source tree for the owned-DIP compact implementation."""
from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import sources
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    dest=HERE/'candidate';assert not dest.exists(),'Preserve existing candidate work'
    baseline=sources()
    for name,digest in baseline.items():
        p=ROOT/name;assert sha(p)==digest
        out=dest/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    # Bring forward the already checked ACH clock implementation as candidate input.
    clock=ROOT/'Verification/build/clock-integration/candidate'
    for name in ('Verification/clock-parts.json','Verification/designs/clock_candidate.py',
                 'Circuits/KiCad/Libraries/DM02-ACH.lib','Verification/hdl/clock_candidate_tb.sv'):
        shutil.copyfile(clock/name,dest/name)
    (HERE/'baseline-sources.json').write_text(json.dumps(baseline,indent=2)+'\n')
    (HERE/'decision.json').write_text(json.dumps(dict(
        goal='Implement owned-DIP IC reductions with pin-derived integrated verification and unchanged milestone criteria.',
        route='Isolated complete source snapshot; compact schematics and explicit models; reuse independent instruction/program oracles.',
        alternatives=['Incrementally change normal sources during an active run','Use only a behavioural CPU model'],
        rationale='Isolation preserves the running normal evidence; actual component/net-derived HDL retains wiring and timing fault detection.',
        jev='Installed guidance unavailable; no advisory result claimed.',
        acceptance=['DIP-only logic and memories','All proposed reduction areas implemented or experimentally rejected with evidence',
                    'Independent KiCad net parity and structural checks','Explicit reset and bus handover checks',
                    'All 227 opcodes, continuous programs and ROM boot','Published exact BOM, evidence and milestone accounting']),indent=2)+'\n')
    assert sources()==baseline
    print('Prepared',len(baseline),'baseline source files')
if __name__=='__main__':main()
