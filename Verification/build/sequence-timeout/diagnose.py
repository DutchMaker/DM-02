"""Replay the exact timed-out binary in isolation and record wall/CPU time."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import resource
import shutil
import subprocess
import time

HERE=Path(__file__).resolve().parent
BUILD=HERE.parent


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination=HERE/'replay'
    assert not destination.exists(),'Refuse to overwrite a diagnostic replay'
    inputs={}
    for relative in ('alu/sequences/slice.vvp','alu/sequences/slice.sv','alu/sequences/sequences.hex','alu/circuit/rom.hex'):
        source=BUILD/relative;target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        inputs[relative]=sha(source);assert sha(target)==inputs[relative]
    started=datetime.now(timezone.utc).isoformat();start=time.monotonic()
    before=resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        result=subprocess.run(['vvp','slice.vvp'],cwd=destination/'alu/sequences',capture_output=True,text=True,timeout=600)
        code=result.returncode;log=result.stdout+result.stderr;timed_out=False
    except subprocess.TimeoutExpired as err:
        code=124;timed_out=True
        log=(err.stdout or b'').decode(errors='replace') if isinstance(err.stdout,bytes) else err.stdout or ''
    wall=time.monotonic()-start;after=resource.getrusage(resource.RUSAGE_CHILDREN)
    (HERE/'replay.log').write_text(log)
    count=sum(1 for _ in (destination/'alu/sequences/sequences.hex').open())
    summary=dict(started_at=started,finished_at=datetime.now(timezone.utc).isoformat(),
        exit_code=code,timed_out=timed_out,wall_seconds=wall,
        cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        source_hashes=inputs,expected_rows=count,timeout_seconds=600,
        passed=code==0 and f'DONE sequences={count}' in log,
        scope='Isolated replay of the failed run binary. Diagnostic only; does not repair or replace the completed full-run report.')
    (HERE/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)


if __name__=='__main__':main()
