"""Export existing filled CD1 copper; run with KiCad's bundled Python.

No fill, geometry repair or board save is performed. Coordinates are mm.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import shutil
import pcbnew as pcb

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'cd1-layout'
ROOT = HERE.parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def xy(point):
    return [pcb.ToMM(point.x), pcb.ToMM(point.y)]


def ring(chain):
    assert chain.ArcCount() == 0, 'Curved polygon requires explicit tessellation'
    return [xy(chain.CPoint(i)) for i in range(chain.PointCount())]


def main():
    global HERE, SOURCE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--out', type=Path, default=HERE)
    parser.add_argument('--board', default='CD1-P0-routed.kicad_pcb')
    args = parser.parse_args()
    HERE, SOURCE = args.out.resolve(), args.source.resolve()
    inputs = HERE / 'inputs'
    inputs.mkdir(parents=True, exist_ok=True)
    paths = [SOURCE / name for name in (
        args.board, 'source.xml', 'validation.json', 'routed-drc.json')]
    paths += [ROOT / 'Verification' / name for name in (
        'distribution-parts.json', 'pc-parts.json', 'vendor/clock/sn74ahct244.txt')]
    hashes = {str(path.relative_to(ROOT)): sha(path) for path in paths}
    for path in paths:
        shutil.copyfile(path, inputs / path.name)
    board_path = inputs / args.board
    board = pcb.LoadBoard(str(board_path))
    assert board.GetCopperLayerCount() == 2
    tracks = []
    vias = []
    for track in board.GetTracks():
        if isinstance(track, pcb.PCB_VIA):
            assert track.GetViaType() == pcb.VIATYPE_THROUGH
            vias.append(dict(id=track.m_Uuid.AsString(), net=track.GetNetname(),
                             position=xy(track.GetPosition()), diameter_mm=pcb.ToMM(track.GetWidth(pcb.F_Cu)),
                             drill_mm=pcb.ToMM(track.GetDrillValue())))
            continue
        assert type(track) is pcb.PCB_TRACK, 'Audit supports straight tracks only'
        tracks.append(dict(id=track.m_Uuid.AsString(), net=track.GetNetname(),
                           layer=board.GetLayerName(track.GetLayer()),
                           start=xy(track.GetStart()), end=xy(track.GetEnd()),
                           width_mm=pcb.ToMM(track.GetWidth()), length_mm=pcb.ToMM(track.GetLength())))
    pads = [dict(ref=fp.GetReference(), pin=pad.GetNumber(), net=pad.GetNetname(),
                 position=xy(pad.GetPosition()), size_mm=xy(pad.GetSize()),
                 drill_mm=xy(pad.GetDrillSize()), through_hole=pad.GetAttribute() == pcb.PAD_ATTRIB_PTH)
            for fp in board.GetFootprints() for pad in fp.Pads()]
    zones = []
    native_samples = []
    for zone in board.Zones():
        assert zone.GetNetname() == '/GND'
        layer = zone.GetLayer()
        polygons = zone.GetFilledPolysList(layer)
        assert polygons.OutlineCount() > 0
        outlines = [dict(shell=ring(polygons.COutline(i)),
                         holes=[ring(polygons.CHole(i, j)) for j in range(polygons.HoleCount(i))])
                    for i in range(polygons.OutlineCount())]
        zones.append(dict(layer=board.GetLayerName(layer), net=zone.GetNetname(), polygons=outlines))
        # Independent native polygon containment values, compared with GEOS later.
        for x in range(21, 80, 2):
            for y in range(21, 90, 2):
                point = pcb.VECTOR2I(pcb.FromMM(x + .137), pcb.FromMM(y + .219))
                native_samples.append(dict(layer=board.GetLayerName(layer), point=xy(point),
                                           inside=bool(polygons.Contains(point))))
        for track in tracks:
            if track['layer'] == board.GetLayerName(layer) or track['net'] in ('/GND', '/5V'):
                continue
            count = max(1, math.ceil(track['length_mm'] / .2))
            for i in range(count):
                fraction = (i + .5) / count
                x, y = [a + fraction * (b - a) for a, b in zip(track['start'], track['end'])]
                point = pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))
                native_samples.append(dict(layer=board.GetLayerName(layer), point=xy(point),
                                           inside=bool(polygons.Contains(point))))
    result = dict(board_file=args.board, board_sha256=sha(board_path), kicad_version=pcb.Version(), input_hashes=hashes,
                  tracks=sorted(tracks, key=lambda t: t['id']), vias=vias, pads=pads, ground_zones=zones,
                  native_zone_samples=native_samples)
    assert all(sha(ROOT / path) == want for path, want in hashes.items())
    (HERE / 'geometry.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'Exported {len(tracks)} tracks, {len(vias)} vias, {len(pads)} pads, {len(zones)} ground fills; source unchanged')


if __name__ == '__main__':
    main()
