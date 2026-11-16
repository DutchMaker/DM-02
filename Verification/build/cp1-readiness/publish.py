"""Publish the independent readiness study and hash its complete evidence tree."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import shutil
import subprocess
import urllib.parse
import urllib.request
from frequency_sweep import HERE,ROOT,sha,write

BASE='https://ruud-macbook-pro-2023.tail668f59.ts.net:8020/build/cp1-readiness/'

def main():
    subprocess.run(['python3',str(HERE/'verify_study.py')],check=True)
    report=ROOT/'Verification/CP1-readiness.md'
    shutil.copyfile(report,HERE/'README.md')
    footer='''
<nav aria-label="Evidence">
<h2>Study files</h2>
<ul>
<li><a href="study-validation.json">Experiment integrity and result index</a></li>
<li><a href="frequency-results.json">Initial proportional-observation matrix</a></li>
<li><a href="capture-results.json">Capture-observed matrix</a></li>
<li><a href="sweep-capture/f5-c1-d0.37-cases1-ppm30/result.json">625 kHz all-opcode receipt</a></li>
<li><a href="timing-screen.json">Conditional path screens</a></li>
<li><a href="README.md">Full study in Markdown</a></li>
<li><a href="../../">Current verification dashboard</a></li>
</ul></nav>
'''
    (HERE/'links.html').write_text(footer)
    subprocess.run(['pandoc',str(report),'--standalone','--toc','--metadata','title=DM-02 CP1-R2 readiness',
        '--css','study.css','--include-after-body',str(HERE/'links.html'),'-o',str(HERE/'index.html')],check=True)
    references=[report,ROOT/'Verification/targets/cp1/lock.json',
        ROOT/'Verification/targets/cp1/overlay/Verification/dm02/compact_hardware.py',
        ROOT/'Verification/targets/cp1/overlay/Verification/designs/compact_candidate.py',
        ROOT/'Verification/targets/cp1/overlay/Verification/clock-parts.json',
        ROOT/'Verification/models.json',ROOT/'Verification/vendor/reset/mcp100.pdf',
        ROOT/'Verification/vendor/alu/m27c322.txt']
    archive=HERE.parent/'cp1-hct273'
    references += [archive/n for n in ('loads.json','physical-review.json','component-review.json','part-qualification.json')]
    references += [archive/'sources'/n for n in ('sn74hct245.txt','um61512a.txt','sn74hc377.txt','cd74hct273.txt','m27c1024.txt','w27c512.txt')]
    write(HERE/'source-references.json',{str(p.relative_to(ROOT)):sha(p) for p in references})
    excluded={'manifest.json','remote-validation.json','browser-check.json','desktop.png','mobile.png'}
    files={str(p.relative_to(HERE)):dict(sha256=sha(p),bytes=p.stat().st_size)
        for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded}
    write(HERE/'manifest.json',dict(files=files,scope='Study integrity; expected failures preserved; no physical acceptance'))
    def check(item):
        name,r=item;h=hashlib.sha256()
        with urllib.request.urlopen(BASE+urllib.parse.quote(name),timeout=90) as response:
            while chunk:=response.read(1024*1024):h.update(chunk)
        assert h.hexdigest()==r['sha256'],name
        return name
    with ThreadPoolExecutor(max_workers=6) as pool:checked=list(pool.map(check,files.items()))
    write(HERE/'remote-validation.json',dict(passed=True,checked_hashes=len(checked),base_url=BASE,manifest_sha256=sha(HERE/'manifest.json')))
    print('Published and verified',len(checked),'files:',BASE)

if __name__=='__main__':main()
