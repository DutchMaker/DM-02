"""Check routed CD1 pad/net identity and exercise native PCB DRC faults."""
from pathlib import Path
from collections import defaultdict
import hashlib
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
PATH=HERE/'CD1-P0-routed.kicad_pcb'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def assignments(board):return {(f.GetReference(),p.GetNumber()):p.GetNetname() for f in board.GetFootprints() for p in f.Pads()}


def main():
    before=digest(PATH);board=pcb.LoadBoard(str(PATH));xml=ET.parse(HERE/'source.xml').getroot()
    expected={(p.attrib['ref'],p.attrib['pin']):n.attrib['name'] for n in xml.findall('./nets/net') for p in n.findall('node')}
    assert assignments(board)==expected
    drc=json.loads((HERE/'routed-drc.json').read_text());assert not drc['violations'] and not drc['unconnected_items']
    assert len(list(board.GetFootprints()))==8 and len(expected)==90
    metrics=defaultdict(lambda:dict(length_mm=0,segments=0,vias=0,layers={}))
    for track in board.GetTracks():
        row=metrics[track.GetNetname()]
        if isinstance(track,pcb.PCB_VIA):row['vias']+=1
        else:
            length=pcb.ToMM(track.GetLength());layer=board.GetLayerName(track.GetLayer())
            row['length_mm']+=length;row['segments']+=1;row['layers'][layer]=row['layers'].get(layer,0)+length
    for row in metrics.values():
        row['length_mm']=round(row['length_mm'],6);row['layers']={k:round(v,6) for k,v in row['layers'].items()}
    folder=HERE/'mutations';folder.mkdir(exist_ok=True);faults=[]
    for fault in ('open-clock','power-short'):
        mutant=pcb.LoadBoard(str(PATH))
        if fault=='open-clock':
            tracks=[t for t in mutant.GetTracks() if t.GetNetname()=='/SQ1_PH0'];assert tracks
            for track in tracks:mutant.Remove(track)
        else:
            cap=next(f for f in mutant.GetFootprints() if f.GetReference()=='C1')
            pads={p.GetNumber():p for p in cap.Pads()}
            track=pcb.PCB_TRACK(mutant);track.SetStart(pads['1'].GetPosition());track.SetEnd(pads['2'].GetPosition())
            track.SetWidth(pcb.FromMM(.25));track.SetLayer(pcb.F_Cu);track.SetNet(pads['1'].GetNet());mutant.Add(track)
        output=folder/(fault+'.kicad_pcb');pcb.SaveBoard(str(output),mutant)
        shutil.copyfile(PATH.with_suffix('.kicad_dru'),output.with_suffix('.kicad_dru'))
        report=folder/(fault+'.json')
        result=subprocess.run(['kicad-cli','pcb','drc',str(output),'--format','json','--output',str(report),
                               '--severity-all','--refill-zones','--exit-code-violations'],capture_output=True,text=True)
        (folder/(fault+'.log')).write_text(result.stdout+result.stderr)
        assert result.returncode==5,(fault,result.stdout,result.stderr)
        finding=json.loads(report.read_text());types=sorted({v['type'] for v in finding['violations']})
        detected=bool(finding['unconnected_items']) if fault=='open-clock' else 'shorting_items' in types
        assert detected,(fault,finding)
        faults.append(dict(fault=fault,detected=detected,unconnected=len(finding['unconnected_items']),violation_types=types))
    mutant=pcb.LoadBoard(str(PATH));connector=next(f for f in mutant.GetFootprints() if f.GetReference()=='J2')
    pad=next(p for p in connector.Pads() if p.GetNumber()=='3');pad.SetNet(mutant.FindNet('/GND'))
    assert assignments(mutant)!=expected
    faults.append(dict(fault='connector-pad-remap',detected=True,checker='Exact native XML versus PCB pad-net comparison'))
    assert digest(PATH)==before
    result=dict(passed=True,board_sha256=before,pad_net_identity=True,components=8,pads=90,nets=30,
        drc_violations=0,unconnected_items=0,drc_ignored_checks=drc['ignored_checks'],
        native_schematic_parity_run=False,net_geometry=dict(sorted(metrics.items())),
        segments=sum(r['segments'] for r in metrics.values()),vias=sum(r['vias'] for r in metrics.values()),
        total_track_length_mm=round(sum(r['length_mm'] for r in metrics.values()),6),
        ground_zones=len(list(board.Zones())),faults=faults,
        scope='Configured native geometric DRC plus exact pad-net comparison and three detected faults. '
              'No complete physical, electrical, manufacturing or connector qualification is implied.',
        fabrication_ready=False)
    (HERE/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CD1 PCB:',result['segments'],'segments;',result['total_track_length_mm'],'mm; zero DRC violations/unconnected; three faults detected')


if __name__=='__main__':main()
