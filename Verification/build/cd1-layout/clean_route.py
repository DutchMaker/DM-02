"""Remove only KiCad-reported dangling tracks after a fully connected import."""
from pathlib import Path
import json
import shutil
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
report=json.loads((HERE/'routed-drc.json').read_text())
assert not report['unconnected_items'] and report['violations']
assert all(v['type']=='track_dangling' for v in report['violations'])
history=HERE/'cleanup.json'
previous=json.loads(history.read_text())['removed'] if history.exists() else []
assert len(previous)<2,'Review geometry before further cleanup'
shutil.copyfile(HERE/'routed-drc.json',HERE/f'routed-before-cleanup-{len(previous)}.json')
path=HERE/'CD1-P0-routed.kicad_pcb';board=pcb.LoadBoard(str(path));removed=[]
for violation in report['violations']:
    for item in violation['items']:
        tracks=[t for t in board.GetTracks() if t.m_Uuid.AsString()==item['uuid']]
        assert len(tracks)==1
        track=tracks[0];assert pcb.ToMM(track.GetLength())<.1,'Review a larger spur manually'
        removed.append(dict(uuid=item['uuid'],net=track.GetNetname(),length_mm=pcb.ToMM(track.GetLength())))
        board.Remove(track)
board.BuildConnectivity();pcb.SaveBoard(str(path),board)
(HERE/'cleanup.json').write_text(json.dumps(dict(removed=previous+removed,reason='KiCad dangling-track warnings; subsequent DRC must prove complete routing and no remaining violations.'),indent=2)+'\n')
print('Removed',len(removed),'reported dangling segment:',removed)
