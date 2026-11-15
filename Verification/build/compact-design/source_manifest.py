"""Freeze the complete candidate source set and select the Git-tracked delta."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    baseline=json.loads((HERE/'baseline-sources.json').read_text());files={};changes={}
    for p in sorted((HERE/'candidate').rglob('*')):
        if not p.is_file():continue
        rel=p.relative_to(HERE/'candidate')
        if '__pycache__' in rel.parts or 'build' in rel.parts:continue
        name=str(rel);h=sha(p);files[name]=h
        if baseline.get(name)!=h:changes[name]=h
    assert set(baseline)<=set(files)
    for name,h in baseline.items():assert sha(ROOT/name)==h,('Normal source changed',name)
    result=dict(baseline_commit='01159e5',normal_sources_unchanged=True,baseline_count=len(baseline),
        candidate_source_count=len(files),candidate_sources=files,candidate_changes=changes)
    (HERE/'source-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(files),'candidate sources;',len(changes),'changed/new;',len(baseline),'normal inputs unchanged')
    return result
if __name__=='__main__':main()
