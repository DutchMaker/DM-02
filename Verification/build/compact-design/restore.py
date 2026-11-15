"""Fill absent unchanged snapshot sources from the pinned Git baseline."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BASE='01159e5'
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
    baseline=json.loads((HERE/'baseline-sources.json').read_text())
    delta=json.loads((HERE/'source-manifest.json').read_text())['candidate_changes']
    restored=0
    for name,h in baseline.items():
        dest=HERE/'candidate'/name
        if name in delta:
            assert dest.exists() and sha(dest.read_bytes())==delta[name],('Missing or edited candidate change',name)
            continue
        if dest.exists():assert sha(dest.read_bytes())==h,('Preserve unexpected local file',name);continue
        data=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT);assert sha(data)==h,name
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);restored+=1
    for name,h in delta.items():assert sha((HERE/'candidate'/name).read_bytes())==h,name
    print('Restored',restored,'unchanged sources; candidate delta hashes verified')
if __name__=='__main__':main()
