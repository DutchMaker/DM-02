import hashlib
import json
import subprocess
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VROOT = ROOT / 'Verification'
BUILD = VROOT / 'build'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    os.replace(temporary, path)


def command(args, cwd=None, timeout=120):
    r = subprocess.run([str(x) for x in args], cwd=cwd or ROOT, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return r.returncode, r.stdout


def evidence(id, title, status, summary, **data):
    assert status in ('pass', 'fail', 'blocked', 'limited', 'error')
    return dict(id=id, title=title, status=status, summary=summary, **data)
