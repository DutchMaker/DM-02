from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib,json,urllib.request,urllib.parse
HERE=Path(__file__).resolve().parent
BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-hct273/'
def check(item):
    name,record=item;h=hashlib.sha256()
    with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
        while chunk:=response.read(1024*1024):h.update(chunk)
    if h.hexdigest()!=record['sha256']:raise ValueError(name)
    return name
def main():
    manifest=json.loads((HERE/'manifest.json').read_text())
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,manifest['files'].items()))
    result=dict(passed=True,checked_hashes=len(checked),base_url=BASE)
    (HERE/'remote-validation.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
