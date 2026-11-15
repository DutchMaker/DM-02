"""Trim the inspected SQ1_PH1 dead-end chain up to its first junction."""
from pathlib import Path
from collections import defaultdict
import json
import shutil
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
path=HERE/'CD1-P0-routed.kicad_pcb';board=pcb.LoadBoard(str(path))
report=json.loads((HERE/'routed-drc.json').read_text())
assert not report['unconnected_items'] and len(report['violations'])==1
violation=report['violations'][0];assert violation['type']=='track_dangling'
uuid=violation['items'][0]['uuid'];tracks={};vertices=defaultdict(list)
point=lambda p:(p.x,p.y)
for track in board.GetTracks():
    if track.GetNetname()!='/SQ1_PH1':continue
    assert not isinstance(track,pcb.PCB_VIA) and track.GetLayer()==pcb.B_Cu
    key=track.m_Uuid.AsString();tracks[key]=track
    vertices[point(track.GetStart())].append(key);vertices[point(track.GetEnd())].append(key)
assert uuid in tracks
first=tracks[uuid];ends=[point(first.GetStart()),point(first.GetEnd())]
starts=[p for p in ends if len(vertices[p])==1];assert len(starts)==1
current=starts[0];previous=None;removed=[]
pads=[pad for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetname()=='/SQ1_PH1']
while len(vertices[current])<3:
    assert not any(pad.HitTest(pcb.VECTOR2I(*current)) for pad in pads),'Dead end touches a pad'
    choices=[key for key in vertices[current] if key!=previous];assert len(choices)==1
    key=choices[0];track=tracks[key];removed.append(track)
    a,b=point(track.GetStart()),point(track.GetEnd());current=b if current==a else a;previous=key
    assert len(removed)<=4,'Unexpected branch topology'
assert len(vertices[current])==3 and len(removed)==2
shutil.copyfile(HERE/'routed-drc.json',HERE/'routed-before-chain-trim.json')
rows=[dict(uuid=t.m_Uuid.AsString(),length_mm=pcb.ToMM(t.GetLength())) for t in removed]
for track in removed:board.Remove(track)
board.BuildConnectivity();pcb.SaveBoard(str(path),board)
(HERE/'chain-trim.json').write_text(json.dumps(dict(net='/SQ1_PH1',removed=rows,
    stop_at_degree_3_junction_mm=[pcb.ToMM(v) for v in current],
    scope='Inspected dead-end chain had no pads. Subsequent DRC must validate complete connectivity.'),indent=2)+'\n')
print('Trimmed dead-end branch:',sum(r['length_mm'] for r in rows),'mm to degree-3 junction')
