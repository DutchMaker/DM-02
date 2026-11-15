"""Stage ACH integration from stable normal sources and the accepted clock study."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CANDIDATE=HERE/'candidate'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import sources


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert not CANDIDATE.exists(),'Refuse to overwrite staged work'
    baseline=sources()
    for relative,digest in baseline.items():
        source=ROOT/relative;assert sha(source)==digest
        target=CANDIDATE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    accepted=ROOT/'Verification/build/clock-ach'
    manifest=json.loads((accepted/'manifest.json').read_text())['files']
    for relative in ('Circuits/KiCad/Libraries/DM02-ACH.lib',
                     'Verification/designs/clock_candidate.py','Verification/hdl/clock_candidate_tb.sv'):
        source=accepted/'sandbox'/relative
        assert sha(source)==manifest['sandbox/'+relative]['sha256']
        target=CANDIDATE/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    parts=json.loads((accepted/'sandbox/Verification/clock-parts.json').read_text())
    parts['revision']='counted-clock-C1-ACH'
    parts['constraints'].update(receiver_duty_min=.37,receiver_duty_max=.63,
        receiver_duty_scope='Assumed digital threshold-duty stress range; the manufacturer only bounds 45/55 duty at half supply.')
    (CANDIDATE/'Verification/clock-parts.json').write_text(json.dumps(parts,indent=2)+'\n')
    vendor=CANDIDATE/'Verification/vendor/clock'
    for name in ('abracon-ach-2016.pdf','abracon-ach-2016.txt','abracon-ach-source.json'):
        source=ROOT/'Verification/build/component-followup'/name
        shutil.copyfile(source,vendor/name)
    (HERE/'baseline-sources.json').write_text(json.dumps(baseline,indent=2)+'\n')
    assert sources()==baseline
    print('Staged',len(baseline),'unchanged normal sources and pinned ACH adaptations')


if __name__=='__main__':main()
