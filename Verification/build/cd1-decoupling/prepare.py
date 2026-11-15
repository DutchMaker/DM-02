"""Archive P2 and exact-part sources for an isolated decoupling experiment."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
URLS={
 'kemet-c315c104k5r5ta.pdf':'https://yageogroup.com/download/specsheet/C315C104K5R5TA',
 'kemet-goldmax-x7r.pdf':'https://yageogroup.com/content/datasheet/asset/file/KEM_C1050_GOLDMAX_X7R',
 'ti-sn74ahct244.pdf':'https://www.ti.com/lit/ds/symlink/sn74ahct244.pdf',
 'ti-n0020a.pdf':'https://www.ti.com/lit/ml/mpdi096/mpdi096.pdf',
 'ti-decoupling-layout.pdf':'https://www.ti.com/content/dam/videos/external-videos/de-de/9/3816841626001/6313253251112.mp4/subassets/notes-decoupling_capacitors.pdf',
}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    dest=HERE/'sources';dest.mkdir(parents=True,exist_ok=True)
    old=json.loads((dest/'manifest.json').read_text()) if (dest/'manifest.json').exists() else {}
    cached={r['file']:r for r in old.get('remote',[])}
    remote=[]
    for name,url in URLS.items():
        path=dest/name
        if name in cached:
            assert sha(path)==cached[name]['sha256'];remote.append(cached[name]);continue
        result=subprocess.run(['curl','-fLsS','--max-time','90','--output',str(path),'--write-out','%{url_effective}',url],capture_output=True,text=True)
        assert result.returncode==0,(url,result.stderr)
        assert path.read_bytes().startswith(b'%PDF'),(url,'not PDF')
        remote.append(dict(file=name,url=url,final_url=result.stdout,retrieved_at=datetime.now(timezone.utc).isoformat(),bytes=path.stat().st_size,sha256=sha(path)))
    local={
      'Verification/build/cd1-stitching/CD1-P2-routed.kicad_pcb':'CD1-P2-routed.kicad_pcb',
      'Verification/build/cd1-stitching/geometry.json':'p2-geometry.json',
      'Verification/build/cd1-stitching/source.xml':'source.xml',
      'Verification/build/cd1-fabrication-screen/CD1-P2-SCREEN-NOT-FOR-FAB.kicad_pro':'screen.kicad_pro',
      'Verification/build/cd1-fabrication-screen/CD1-P2-SCREEN-NOT-FOR-FAB.kicad_dru':'screen.kicad_dru',
      'Verification/build/cd1-fabrication-screen/supplier-facts.json':'supplier-facts.json',
      'Verification/build/cd1-electrical/analyze.py':'ground-audit.py',
      'Verification/build/cd1-fabrication-screen/audit_cam.py':'cam-parser.py',
    }
    rows=[]
    for original,name in local.items():
        path=dest/name
        if path.exists():assert sha(path)==sha(ROOT/original)
        else:shutil.copyfile(ROOT/original,path)
        rows.append(dict(file=name,source=original,sha256=sha(path)))
    (dest/'manifest.json').write_text(json.dumps(dict(remote=remote,local=rows),indent=2)+'\n')
    print('Archived',len(remote),'manufacturer sources and',len(rows),'local inputs')


if __name__=='__main__':main()
