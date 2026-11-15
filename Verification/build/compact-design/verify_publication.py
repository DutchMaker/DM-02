"""Hash every published artifact locally and over the existing Tailscale URL."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,urllib.request,urllib.parse
HERE=Path(__file__).resolve().parent
def main(folder=HERE):
    folder=Path(folder).resolve();build=HERE.parent
    base='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/'+str(folder.relative_to(build))+'/'
    def fetch(name):
        with urllib.request.urlopen(base+urllib.parse.quote(name),timeout=120) as f:return f.read()
    manifest=json.loads((folder/'manifest.json').read_text());assert fetch('manifest.json')==(folder/'manifest.json').read_bytes()
    def check(item):
        name,row=item;local=(folder/name).read_bytes();assert len(local)==row['bytes'] and hashlib.sha256(local).hexdigest()==row['sha256'],name
        remote=fetch(name);assert len(remote)==row['bytes'] and hashlib.sha256(remote).hexdigest()==row['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,manifest['files'].items()))
    result=dict(passed=True,base=base,checked=len(checked),manifest_sha256=hashlib.sha256((folder/'manifest.json').read_bytes()).hexdigest())
    (folder/'remote-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',nargs='?',default=HERE);a=p.parse_args();main(a.folder)
