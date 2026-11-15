"""Native PCB checks accepting KiCad's equivalent power-short diagnostics."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE = Path(__file__).resolve().parent
PATH = HERE / 'CD1-P2-routed.kicad_pcb'


def assignments(board):
    return {(f.GetReference(), p.GetNumber()): p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}


def main():
    before = hashlib.sha256(PATH.read_bytes()).hexdigest()
    board = pcb.LoadBoard(str(PATH))
    xml = ET.parse(HERE / 'source.xml').getroot()
    expected = {(p.attrib['ref'], p.attrib['pin']): n.attrib['name']
                for n in xml.findall('./nets/net') for p in n.findall('node')}
    assert assignments(board) == expected
    assert len(expected) == 90 and len(list(board.GetFootprints())) == 8
    drc = json.loads((HERE / 'routed-drc.json').read_text())
    assert not drc['violations'] and not drc['unconnected_items']
    metrics = defaultdict(lambda: dict(length_mm=0., segments=0, vias=0, layers={}))
    for track in board.GetTracks():
        row = metrics[track.GetNetname()]
        if isinstance(track, pcb.PCB_VIA):
            row['vias'] += 1
        else:
            length, layer = pcb.ToMM(track.GetLength()), board.GetLayerName(track.GetLayer())
            row['length_mm'] += length
            row['segments'] += 1
            row['layers'][layer] = row['layers'].get(layer, 0) + length
    folder = HERE / 'mutations'
    folder.mkdir(exist_ok=True)
    faults = []
    for fault in ('open-clock', 'power-short'):
        mutant = pcb.LoadBoard(str(PATH))
        if fault == 'open-clock':
            tracks = [t for t in mutant.GetTracks() if t.GetNetname() == '/SQ1_PH0']
            assert tracks
            for track in tracks:
                mutant.Remove(track)
        else:
            cap = next(f for f in mutant.GetFootprints() if f.GetReference() == 'C1')
            pads = {p.GetNumber(): p for p in cap.Pads()}
            track = pcb.PCB_TRACK(mutant)
            track.SetStart(pads['1'].GetPosition())
            track.SetEnd(pads['2'].GetPosition())
            track.SetWidth(pcb.FromMM(.25))
            track.SetLayer(pcb.F_Cu)
            track.SetNet(pads['1'].GetNet())
            mutant.Add(track)
        output = folder / (fault + '.kicad_pcb')
        pcb.SaveBoard(str(output), mutant)
        stored = pcb.LoadBoard(str(output))
        assert assignments(stored) == expected
        if fault == 'open-clock':
            assert all(t.GetNetname() != '/SQ1_PH0' for t in stored.GetTracks())
        else:
            saved_track = next(t for t in stored.GetTracks() if t.m_Uuid.AsString() == track.m_Uuid.AsString())
            assert saved_track.GetNetname() == '/5V' and saved_track.GetLength() == pcb.FromMM(5)
        shutil.copyfile(PATH.with_suffix('.kicad_dru'), output.with_suffix('.kicad_dru'))
        report = output.with_suffix('.json')
        result = subprocess.run(['kicad-cli', 'pcb', 'drc', str(output), '--format', 'json',
                                 '--output', str(report), '--severity-all', '--refill-zones',
                                 '--exit-code-violations'], capture_output=True, text=True)
        output.with_suffix('.log').write_text(result.stdout+result.stderr)
        finding = json.loads(report.read_text())
        assert result.returncode == 5
        if fault == 'open-clock':
            detected = bool(finding['unconnected_items'])
        else:
            # KiCad can report this same persisted fault as a short or a crossing.
            # Require both supply nets in the actual electrical diagnostic items.
            detected = any(v['type'] in ('shorting_items', 'tracks_crossing') and
                           all(any(f'[{net}]' in item['description'] for item in v['items'])
                               for net in ('/5V', '/GND')) for v in finding['violations'])
        assert detected, finding
        faults.append(dict(fault=fault, detected=True, persisted=True,
                           unconnected=len(finding['unconnected_items']),
                           violation_types=sorted({v['type'] for v in finding['violations']})))
    mutant = pcb.LoadBoard(str(PATH))
    pad = next(p for f in mutant.GetFootprints() if f.GetReference() == 'J2' for p in f.Pads() if p.GetNumber() == '3')
    pad.SetNet(mutant.FindNet('/GND'))
    assert assignments(mutant) != expected
    faults.append(dict(fault='connector-pad-remap', detected=True, checker='Exact native XML versus PCB pad-net comparison'))
    assert hashlib.sha256(PATH.read_bytes()).hexdigest() == before
    result = dict(passed=True, board_sha256=before, pad_net_identity=True, components=8, pads=90, nets=30,
                  drc_violations=0, unconnected_items=0, drc_ignored_checks=drc['ignored_checks'],
                  native_schematic_parity_run=False, net_geometry=dict(sorted(metrics.items())),
                  segments=sum(r['segments'] for r in metrics.values()),
                  vias=sum(r['vias'] for r in metrics.values()),
                  total_track_length_mm=sum(r['length_mm'] for r in metrics.values()),
                  ground_zones=len(list(board.Zones())), faults=faults, fabrication_ready=False)
    (HERE / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print('P2 native DRC and three existing faults pass')


if __name__ == '__main__':
    main()
