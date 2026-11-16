"""Promote only a fully accepted, published CP1-R2 source/evidence set."""
from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2];BUILD=ROOT/'Verification/build';TARGET=ROOT/'Verification/targets/cp1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
    parent=read(HERE/'parent-lock.json');current=read(TARGET/'lock.json')
    if current!=parent:raise RuntimeError('Active CP1 lock changed since staging; inspect before promotion')
    accepted=read(HERE/'acceptance.json')
    assert accepted['passed'] and accepted['full_digital_rerun'] and accepted['selected_273']=='CD74HCT273E'
    for name,h in accepted['key_receipt_sha256'].items():assert sha(HERE/name)==h,name
    for flag in ('remote-validation.json','browser-check.json'):assert read(HERE/flag)['passed'],flag
    manifest=read(HERE/'manifest.json')
    for name,record in manifest['files'].items():assert sha(HERE/name)==record['sha256'],name
    sources=read(HERE/'source-manifest.json')
    for name,h in current['sources'].items():
        origin=TARGET/'overlay'/name if name in current['overlay'] else ROOT/name
        assert sha(origin)==h,('Active input changed',name)
    for name,h in sources['candidate_sources'].items():assert sha(HERE/'candidate'/name)==h,name
    delta=sources['revision_changes'];assert set(delta)<=set(current['overlay'])
    for name,h in delta.items():
        shutil.copyfile(HERE/'candidate'/name,TARGET/'overlay'/name)
        assert sha(TARGET/'overlay'/name)==h
    lock=dict(current)
    lock.update(revision='CP1-R2',evidence_directory='cp1-hct273',
                release='https://github.com/DutchMaker/DM-02/releases/tag/cp1-hct273-2026-11-16',
                sources=sources['candidate_sources'],previous_lock_sha256=sha(HERE/'parent-lock.json'))
    reference_prefix=str(Path(current['reference_report']).parent)+'/'
    artifacts={n:h for n,h in current['artifacts'].items() if n.startswith(reference_prefix)}
    artifacts.update({'cp1-hct273/'+n:r['sha256'] for n,r in manifest['files'].items()})
    for name in ('manifest.json','parent-lock.json','remote-validation.json','browser-check.json'):
        artifacts['cp1-hct273/'+name]=sha(HERE/name)
    lock['artifacts']=dict(sorted(artifacts.items()))
    lock['decision']='CP1-R2: documented CD74HCT273E delay bounds, explicit 3 ns hold monitor, full digital rerun and unchanged physical acceptance criteria.'
    temporary=TARGET/'lock.json.tmp';temporary.write_text(json.dumps(lock,indent=2)+'\n');temporary.replace(TARGET/'lock.json')
    print('Promoted',len(delta),'source changes and',len(artifacts),'locked artifacts')
if __name__=='__main__':main()
