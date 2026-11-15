"""Preserve the second completed normal run, including its demo timeout."""
from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];BUILD=HERE.parent
TARGET=BUILD/'experiments/2026-11-15-analog-retry-timeout'
sys.path.insert(0,str(ROOT/'Verification'))
from dm02.reporting import freshness
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    live=BUILD/'report.json';raw=live.read_bytes();r=json.loads(raw)
    assert freshness(r)['fresh'] and r['state']=='complete'
    errors=[c for c in r['checks'] if c['status']=='error']
    assert {c['id'] for c in errors}=={'hardware-programs','boot'}
    assert '3600 seconds' in next(c['summary'] for c in errors if c['id']=='hardware-programs')
    assert not TARGET.exists(),'Preserve previous archive'
    inputs=[(live,'report.json',sha(live))]+[(ROOT/p,'sources/'+p,h) for p,h in r['source_hashes'].items()]+[(BUILD/p,p,h) for p,h in r['artifact_hashes'].items()]
    rows={}
    for src,name,h in inputs:
        assert sha(src)==h,src
        dst=TARGET/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst);assert sha(dst)==h
        rows[name]=dict(bytes=dst.stat().st_size,sha256=h)
    assert live.read_bytes()==raw and freshness(r)['fresh']
    summary=dict(finished_at=r['finished_at'],errors=errors,status_counts=dict(Counter(c['status'] for c in r['checks'])),
        milestones=r['milestones'],acceptance_complete=False,hashes_verified=True,
        scope='Normal analogue retry: hardware-programs exceeded 3600 seconds; boot dependency blocked. No identical retry scheduled. Compact CP1 has separate inputs and evidence.')
    (TARGET/'archive.json').write_text(json.dumps(summary,indent=2)+'\n')
    rows['archive.json']=dict(bytes=(TARGET/'archive.json').stat().st_size,sha256=sha(TARGET/'archive.json'))
    (TARGET/'manifest.json').write_text(json.dumps(dict(files=rows),indent=2)+'\n')
    print('Preserved normal retry:',len(rows),'verified files')
if __name__=='__main__':main()
