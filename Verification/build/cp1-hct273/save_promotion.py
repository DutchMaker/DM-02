"""Preserve the accepted live report and its otherwise mutable replay logs."""
from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
BUILD=HERE.parent
sys.path.insert(0,str(BUILD.parent))
from dm02.reporting import freshness
from dm02.cp1 import verify_hashes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    source=BUILD/'report.json';raw=source.read_text();report=json.loads(raw)
    assert report['revision']=='CP1-R2' and report['state']=='complete' and freshness(report)['fresh']
    assert not any(c['status']=='error' for c in report['checks'])
    verify_hashes(BUILD,report['artifact_hashes'])
    dest=HERE/'promotion';dest.mkdir(exist_ok=True)
    mapping={'cp1/'+name:'cp1-hct273/promotion/'+name for name in ('equivalence.json','equivalence.log','smoke.log')}
    mapping['tests.log']='cp1-hct273/promotion/tests.log'
    for old,new in mapping.items():
        shutil.copyfile(BUILD/old,BUILD/new)
        assert sha(BUILD/new)==report['artifact_hashes'][old]
    (dest/'original-report.json').write_text(raw)
    report['artifact_hashes']={mapping.get(n,n):h for n,h in report['artifact_hashes'].items()}
    for c in report['checks']:c['artifacts']=[mapping.get(n,n) for n in c.get('artifacts',[])]
    report['equivalence']['fresh_smoke']['log']='cp1-hct273/promotion/smoke.log'
    report['archival_scope']='Promoted CP1-R2 report with copied replay/harness logs. Original live report retained verbatim. Earlier reference and original CP1 releases remain unchanged.'
    (dest/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    files={p.name:sha(p) for p in dest.iterdir() if p.is_file() and p.name!='manifest.json'}
    (dest/'manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print('Saved promotion:',len(files),'files;',next(c['summary'] for c in report['checks'] if c['id']=='harness'))
if __name__=='__main__':main()
