"""Add the planned ground vias to a copy of CD1-P1; verify native DRC."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import pcbnew as pcb

HERE = Path(__file__).resolve().parent
SOURCES = HERE / 'sources'
BOARD = HERE / 'CD1-P2-routed.kicad_pcb'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def track_signature(t):
    if isinstance(t, pcb.PCB_VIA):
        return (t.GetNetname(), t.GetPosition().x, t.GetPosition().y, t.GetWidth(pcb.F_Cu),
                t.GetDrillValue(), t.GetViaType(), t.TopLayer(), t.BottomLayer())
    return (t.GetNetname(), t.GetLayer(), t.GetStart().x, t.GetStart().y,
            t.GetEnd().x, t.GetEnd().y, t.GetWidth())


def pad_signatures(board):
    return {(f.GetReference(), p.GetNumber()): (p.GetNetname(), p.GetPosition().x, p.GetPosition().y,
             p.GetSize().x, p.GetSize().y, p.GetDrillSize().x, p.GetDrillSize().y,
             p.GetShape(), p.GetOrientationDegrees()) for f in board.GetFootprints() for p in f.Pads()}


def drc(path, report):
    result = subprocess.run(['kicad-cli', 'pcb', 'drc', str(path), '--format', 'json',
                             '--output', str(report), '--severity-all', '--refill-zones',
                             '--exit-code-violations'], capture_output=True, text=True)
    report.with_suffix('.log').write_text(result.stdout+result.stderr)
    return result.returncode, json.loads(report.read_text())


def check_stitches(board, additions, plan):
    vias = {t.m_Uuid.AsString(): t for t in board.GetTracks() if isinstance(t, pcb.PCB_VIA)}
    for row in additions:
        assert row['uuid'] in vias, f'Missing stitch {row["id"]}'
        via = vias[row['uuid']]
        assert via.GetNetname() == '/GND', f'Wrong stitch net {row["id"]}'
        assert [round(pcb.ToMM(v), 6) for v in (via.GetPosition().x, via.GetPosition().y)] == row['position']
        assert via.GetWidth(pcb.F_Cu) == pcb.FromMM(plan['via_diameter_mm'])
        assert via.GetDrillValue() == pcb.FromMM(plan['via_drill_mm'])
        assert via.TopLayer() == pcb.F_Cu and via.BottomLayer() == pcb.B_Cu


def main():
    plan = json.loads((HERE / 'plan.json').read_text())
    original = SOURCES / 'CD1-P1-routed.kicad_pcb'
    assert sha(original) == plan['baseline_sha256']
    board = pcb.LoadBoard(str(original))
    old_tracks = {t.m_Uuid.AsString(): track_signature(t) for t in board.GetTracks()}
    old_pads = pad_signatures(board)
    additions = []
    for row in plan['new_ground_vias']:
        via = pcb.PCB_VIA(board)
        via.SetPosition(pcb.VECTOR2I(*(pcb.FromMM(v) for v in row['position'])))
        via.SetViaType(pcb.VIATYPE_THROUGH)
        via.SetLayerPair(pcb.F_Cu, pcb.B_Cu)
        via.SetWidth(pcb.FromMM(plan['via_diameter_mm']))
        via.SetDrill(pcb.FromMM(plan['via_drill_mm']))
        via.SetNet(board.FindNet('/GND'))
        board.Add(via)
        additions.append(dict(**row, uuid=via.m_Uuid.AsString()))
    for item in board.GetDrawings():
        if isinstance(item, pcb.PCB_TEXT) and item.GetText() == 'DM-02 CD1-P1':
            item.SetText('DM-02 CD1-P2')
    board.BuildConnectivity()
    pcb.ZONE_FILLER(board).Fill(board.Zones())
    pcb.SaveBoard(str(BOARD), board)
    for suffix in ('.kicad_dru', '.kicad_pro'):
        shutil.copyfile(original.with_suffix(suffix), BOARD.with_suffix(suffix))
    for name in ('source.xml', 'source.kicad_sch'):
        shutil.copyfile(SOURCES / name, HERE / name)
    code, findings = drc(BOARD, HERE / 'routed-drc.json')
    assert code == 0 and not findings['violations'] and not findings['unconnected_items'], findings
    spec = importlib.util.spec_from_file_location('pcb_check', HERE / 'check_board.py')
    check = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(check)
    check.HERE, check.PATH = HERE, BOARD
    check.main()
    after = pcb.LoadBoard(str(BOARD))
    new_tracks = {t.m_Uuid.AsString(): track_signature(t) for t in after.GetTracks()}
    assert all(new_tracks[k] == v for k, v in old_tracks.items())
    assert set(new_tracks)-set(old_tracks) == {r['uuid'] for r in additions}
    assert pad_signatures(after) == old_pads
    check_stitches(after, additions, plan)
    assert sha(original) == plan['baseline_sha256']
    # A wrong-net stitch can evade DRC after refill; the intent contract must reject it.
    wrong = pcb.LoadBoard(str(BOARD))
    target = next(t for t in wrong.GetTracks() if t.m_Uuid.AsString() == additions[0]['uuid'])
    # Normal vias inherit copper connectivity on save. Free vias preserve this
    # deliberately incorrect assignment so the stored fault is real.
    target.SetIsFree(True)
    target.SetNet(wrong.FindNet('/5V'))
    mutant = HERE / 'mutations' / 'stitch-to-5v.kicad_pcb'
    pcb.SaveBoard(str(mutant), wrong)
    stored_wrong = pcb.LoadBoard(str(mutant))
    stored_target = next(t for t in stored_wrong.GetTracks() if t.m_Uuid.AsString() == additions[0]['uuid'])
    assert stored_target.GetNetname() == '/5V' and stored_target.GetIsFree()
    shutil.copyfile(BOARD.with_suffix('.kicad_dru'), mutant.with_suffix('.kicad_dru'))
    code, fault = drc(mutant, mutant.with_suffix('.json'))
    types = sorted({v['type'] for v in fault['violations']})
    assert code in (0, 5), fault
    try:
        check_stitches(pcb.LoadBoard(str(mutant)), additions, plan)
    except AssertionError as error:
        wrong_net_diagnostic = str(error)
    else:
        raise AssertionError('Stitch net mutation escaped the intent contract')
    omissions = []
    for addition in additions:
        missing = pcb.LoadBoard(str(BOARD))
        missing.Remove(next(t for t in missing.GetTracks() if t.m_Uuid.AsString() == addition['uuid']))
        missing_path = HERE / 'mutations' / f'missing-{addition["id"]}.kicad_pcb'
        pcb.SaveBoard(str(missing_path), missing)
        missing = pcb.LoadBoard(str(missing_path))
        assert all(t.m_Uuid.AsString() != addition['uuid'] for t in missing.GetTracks())
        try:
            check_stitches(missing, additions, plan)
        except AssertionError as error:
            omissions.append(dict(stitch=addition['id'], detected=True, diagnostic=str(error)))
        else:
            raise AssertionError('Missing stitch escaped the intent contract')
    report = dict(baseline_sha256=plan['baseline_sha256'], candidate_sha256=sha(BOARD),
                  added_ground_vias=additions, preserved_track_objects=len(old_tracks),
                  preserved_pads=len(old_pads), pad_net_and_geometry_unchanged=True,
                  all_original_track_objects_unchanged=True, original_unchanged=True,
                  wrong_net_stitch_detected=True, wrong_net_stitch_drc_types=types,
                  wrong_net_stitch_drc_exit=code, wrong_net_stitch_drc_detected=bool(fault['violations'] or fault['unconnected_items']),
                  wrong_net_stitch_intent_diagnostic=wrong_net_diagnostic, missing_stitch_mutations=omissions,
                  wrong_net_mutation_persisted=True, wrong_net_via_free_flag=True,
                  fabrication_ready=False)
    (HERE / 'change.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'P2 adds {len(additions)} ground vias; preserves {len(old_tracks)} track/via objects and {len(old_pads)} pads; clean DRC, three original faults and nine stitch intent faults detected')


if __name__ == '__main__':
    main()
