"""Export stored P3 copper and native containment samples without rewriting it."""
from pathlib import Path
import hashlib
import json
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
BOARD=HERE/'CD1-P3-decoupling.kicad_pcb'
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def ring(c):
    assert c.ArcCount()==0
    return [xy(c.CPoint(i)) for i in range(c.PointCount())]


def main():
    b=pcb.LoadBoard(str(BOARD));tracks=[];vias=[];zones=[];samples=[]
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA):
            vias.append(dict(id=t.m_Uuid.AsString(),position=xy(t.GetPosition()),net=t.GetNetname(),
                diameter_mm=pcb.ToMM(t.GetWidth(pcb.F_Cu)),drill_mm=pcb.ToMM(t.GetDrillValue())))
        else:tracks.append(dict(id=t.m_Uuid.AsString(),net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),
            start=xy(t.GetStart()),end=xy(t.GetEnd()),width_mm=pcb.ToMM(t.GetWidth()),length_mm=pcb.ToMM(t.GetLength())))
    pads=[dict(ref=f.GetReference(),pin=p.GetNumber(),net=p.GetNetname(),position=xy(p.GetPosition()),
        size_mm=xy(p.GetSize()),drill_mm=xy(p.GetDrillSize()),shape=int(p.GetShape()),
        through_hole=p.GetAttribute()==pcb.PAD_ATTRIB_PTH) for f in b.GetFootprints() for p in f.Pads()]
    for z in b.Zones():
        assert z.GetNetname()=='/GND';polys=z.GetFilledPolysList(z.GetLayer());layer=b.GetLayerName(z.GetLayer())
        zones.append(dict(layer=layer,net=z.GetNetname(),polygons=[dict(shell=ring(polys.COutline(i)),
            holes=[ring(polys.CHole(i,j)) for j in range(polys.HoleCount(i))]) for i in range(polys.OutlineCount())]))
        points=[[x+.137,y+.219] for x in range(21,80) for y in range(21,90)]
        for p in pads:
            if p['ref'].startswith('C'):
                points += [[p['position'][0]+dx/10,p['position'][1]+dy/10] for dx in range(-12,13,2) for dy in range(-12,13,2)]
        for x,y in points:
            samples.append(dict(layer=layer,point=[x,y],inside=bool(polys.Contains(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))))))
    edges=[dict(start=xy(d.GetStart()),end=xy(d.GetEnd()),width_mm=pcb.ToMM(d.GetWidth()))
           for d in b.GetDrawings() if d.GetLayer()==pcb.Edge_Cuts]
    assert len(edges)==4
    (HERE/'geometry.json').write_text(json.dumps(dict(board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),
        tracks=tracks,vias=vias,pads=pads,ground_zones=zones,native_zone_samples=samples,outline=edges),indent=2)+'\n')
    print(len(tracks),'tracks;',len(vias),'vias;',len(samples),'native containment samples')


if __name__=='__main__':main()
