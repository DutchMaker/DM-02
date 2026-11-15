"""CD1-P1: replace ROOT2_0's broadside duplicate branch with one via.

Run with KiCad Python. P0 is hash-checked and never written.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import pcbnew as pcb

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'cd1-layout'
DEST = HERE / 'candidate'
BASE_HASH = '359f195e227a0f0d938c5bde2d3d5b2fac7239c7d1f01c693e42a6579debf00a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = SOURCE / 'CD1-P0-routed.kicad_pcb'
    assert sha(original) == BASE_HASH
    DEST.mkdir(exist_ok=True)
    target = DEST / 'CD1-P1-routed.kicad_pcb'
    board = pcb.LoadBoard(str(original))
    tracks = list(board.GetTracks())
    remove = next(t for t in tracks if t.m_Uuid.AsString() == '51302964-ae4e-4792-ac33-9d5408140785')
    assert remove.GetNetname() == '/ROOT2_0' and remove.GetLayer() == pcb.F_Cu
    junction = remove.GetEnd()
    assert pcb.ToMM(junction.x) == 54.3638 and pcb.ToMM(junction.y) == 57.1162
    length = pcb.ToMM(remove.GetLength())
    board.Remove(remove)
    via = pcb.PCB_VIA(board)
    via.SetPosition(junction)
    via.SetViaType(pcb.VIATYPE_THROUGH)
    via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
    via.SetWidth(pcb.FromMM(.8))
    via.SetDrill(pcb.FromMM(.4))
    via.SetNet(board.FindNet('/ROOT2_0'))
    board.Add(via)
    for item in board.GetDrawings():
        if isinstance(item, pcb.PCB_TEXT) and item.GetText() == 'DM-02 CD1-P0':
            item.SetText('DM-02 CD1-P1')
    board.BuildConnectivity()
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(target), board)
    for suffix in ('.kicad_dru', '.kicad_pro'):
        shutil.copyfile(original.with_suffix(suffix), target.with_suffix(suffix))
    for name in ('source.xml', 'source.kicad_sch'):
        shutil.copyfile(SOURCE / name, DEST / name)
    cmd = ['kicad-cli', 'pcb', 'drc', str(target), '--format', 'json', '--output', str(DEST / 'routed-drc.json'),
           '--severity-all', '--refill-zones', '--exit-code-violations']
    result = subprocess.run(cmd, capture_output=True, text=True)
    (DEST / 'drc.log').write_text(result.stdout + result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    spec = importlib.util.spec_from_file_location('cd1_check', SOURCE / 'check.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE, module.PATH = DEST, target
    module.main()
    after = pcb.LoadBoard(str(target))
    old_assignments = module.assignments(pcb.LoadBoard(str(original)))
    assert module.assignments(after) == old_assignments
    new_tracks = list(after.GetTracks())
    old_map = {t.m_Uuid.AsString(): t for t in tracks}
    new_map = {t.m_Uuid.AsString(): t for t in new_tracks}
    assert set(old_map) - set(new_map) == {remove.m_Uuid.AsString()}
    assert set(new_map) - set(old_map) == {via.m_Uuid.AsString()}
    def signature(t):
        return (t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y,
                t.GetEnd().x, t.GetEnd().y, t.GetWidth())
    assert all(signature(old_map[k]) == signature(new_map[k]) for k in set(old_map) & set(new_map))
    # The new layer transition is electrically necessary; exercise its removal.
    missing = pcb.LoadBoard(str(target))
    missing.Remove(next(t for t in missing.GetTracks() if t.m_Uuid.AsString() == via.m_Uuid.AsString()))
    mutation = DEST / 'mutations' / 'missing-branch-via.kicad_pcb'
    pcb.SaveBoard(str(mutation), missing)
    shutil.copyfile(target.with_suffix('.kicad_dru'), mutation.with_suffix('.kicad_dru'))
    fault_report = mutation.with_suffix('.json')
    fault = subprocess.run(['kicad-cli', 'pcb', 'drc', str(mutation), '--format', 'json',
                            '--output', str(fault_report), '--severity-all', '--refill-zones',
                            '--exit-code-violations'], capture_output=True, text=True)
    mutation.with_suffix('.log').write_text(fault.stdout + fault.stderr)
    findings = json.loads(fault_report.read_text())
    assert fault.returncode == 5 and findings['unconnected_items']
    assert sha(original) == BASE_HASH
    report = dict(original_sha256=BASE_HASH, candidate_sha256=sha(target),
                  removed_track_id=remove.m_Uuid.AsString(), removed_track_length_mm=length,
                  added_via_id=via.m_Uuid.AsString(), via_position_mm=[54.3638, 57.1162],
                  via_diameter_mm=.8, via_drill_mm=.4, preserved_tracks=len(set(old_map) & set(new_map)),
                  exact_pad_net_identity=True, original_unchanged=True,
                  missing_branch_via_detected=True,
                  missing_branch_via_unconnected_items=len(findings['unconnected_items']),
                  scope='One local routing substitution; physical qualification remains open.')
    (DEST / 'change.json').write_text(json.dumps(report, indent=2) + '\n')
    print('P1 removes', length, 'mm and adds one through via; DRC and four mutations pass')


if __name__ == '__main__':
    main()
