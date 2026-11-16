"""Pin the complete CP1-R2 input set and its precise delta from accepted CP1."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parent=json.loads((HERE.parent/'compact-design/source-manifest.json').read_text())
    files={name:sha(HERE/'candidate'/name) for name in parent['candidate_sources']}
    changes={name:h for name,h in files.items() if parent['candidate_sources'][name]!=h}
    expected={'Circuits/KiCad/Compact/candidates/AL1.sch','Circuits/KiCad/Compact/candidates/ME1.sch',
              'Verification/designs/compact_candidate.py','Verification/dm02/compact_hardware.py','Verification/hdl/compact_devices.sv'}
    assert set(changes)==expected,changes
    baseline=json.loads((HERE.parent/'compact-design/baseline-sources.json').read_text())
    result=dict(revision='CP1-R2',parent_release='compact-design-2026-11-16',baseline_commit=parent['baseline_commit'],
                candidate_source_count=len(files),candidate_sources=files,revision_changes=changes,
                candidate_changes={n:h for n,h in files.items() if baseline.get(n)!=h})
    (HERE/'source-manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(len(files),'sources;',len(changes),'revision changes')
if __name__=='__main__':main()
