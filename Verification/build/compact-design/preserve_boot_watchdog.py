"""Preserve the ROM-boot run stopped by the inherited simulated-time limit."""
from pathlib import Path
import hashlib,json,shutil
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'candidate/Verification/build/compact/c1-boot'
DEST=HERE/'failed-runs/boot-watchdog-4s'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    result=json.loads((SOURCE/'result.json').read_text());log=(SOURCE/'simulation.log').read_text()
    assert not result['passed'] and result['exit_code']==1 and 'SQ watchdog' in log
    assert 'DONE BL1 payload_bytes=16542 writes=24326' in log
    assert not DEST.exists(),'Preserve existing failed-run archive'
    shutil.copytree(SOURCE,DEST/'simulation')
    for name in ('run.py','resume.py','resume.log','verification-state.json'):shutil.copyfile(HERE/name,DEST/name)
    coverage=result['coverage'];minimum_ns=coverage['microcycles']*8*250
    assert minimum_ns>4_000_000_000
    receipt=dict(acceptance_complete=False,reason='Inherited DEMO simulated-time watchdog is shorter than the known CP1 program schedule.',
        expected_microcycles=coverage['microcycles'],nominal_microcycle_ns=2000,minimum_schedule_ns=minimum_ns,
        inherited_watchdog_ns=4_000_000_000,wall_timeout_seconds=result['timeout_seconds'],wall_seconds=result['wall_seconds'],
        loader_payload_bytes=16542,loader_sram_writes=24326,loader_checked=True,graphics_halt_checked=False)
    (DEST/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    files={str(p.relative_to(DEST)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(DEST.rglob('*')) if p.is_file()}
    (DEST/'manifest.json').write_text(json.dumps(dict(files=files),indent=2)+'\n')
    print('Preserved',len(files),'files;',receipt)
if __name__=='__main__':main()
