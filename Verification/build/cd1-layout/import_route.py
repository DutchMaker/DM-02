"""Import local autorouting; retain net assignments and report native geometry."""
from pathlib import Path
from collections import defaultdict
import json
import shutil
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE=Path(__file__).resolve().parent


def point(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))


def main():
    source=HERE/'CD1-P0.kicad_pcb';output=HERE/'CD1-P0-routed.kicad_pcb'
    board=pcb.LoadBoard(str(source));assert pcb.ImportSpecctraSES(board,str(HERE/'CD1-P0.ses'))
    xml=ET.parse(HERE/'source.xml').getroot()
    expected={(pin.attrib['ref'],pin.attrib['pin']):net.attrib['name'] for net in xml.findall('./nets/net') for pin in net.findall('node')}
    actual={(fp.GetReference(),pad.GetNumber()):pad.GetNetname() for fp in board.GetFootprints() for pad in fp.Pads()}
    assert expected==actual
    components={c.attrib['ref']:(c.findtext('value'),c.findtext('footprint')) for c in xml.findall('./components/comp')}
    assert components=={fp.GetReference():(fp.GetValue(),fp.GetFPID().GetUniStringLibId()) for fp in board.GetFootprints()}
    # Ground pours supplement the routed ground tree. Return-path quality is
    # an electrical review item; DRC does not measure impedance or capacitance.
    ground=board.FindNet('/GND')
    for layer in (pcb.F_Cu,pcb.B_Cu):
        zone=pcb.ZONE(board);zone.SetLayer(layer);zone.SetNet(ground)
        zone.SetLocalClearance(pcb.FromMM(.25));zone.SetMinThickness(pcb.FromMM(.25))
        zone.SetThermalReliefGap(pcb.FromMM(.3));zone.SetThermalReliefSpokeWidth(pcb.FromMM(.3))
        zone.SetPadConnection(pcb.ZONE_CONNECTION_THERMAL)
        outline=zone.Outline();outline.NewOutline()
        for x,y in ((20.5,20.5),(79.5,20.5),(79.5,89.5),(20.5,89.5)):outline.Append(pcb.FromMM(x),pcb.FromMM(y))
        board.Add(zone)
    board.BuildConnectivity();pcb.SaveBoard(str(output),board)
    shutil.copyfile(HERE/'CD1-P0.kicad_dru',output.with_suffix('.kicad_dru'))
    totals=defaultdict(lambda:dict(segments=0,length_mm=0,via_count=0,layers={}))
    for track in board.GetTracks():
        row=totals[track.GetNetname()]
        if isinstance(track,pcb.PCB_VIA):row['via_count']+=1
        else:
            length=pcb.ToMM(track.GetLength());layer=board.GetLayerName(track.GetLayer())
            row['segments']+=1;row['length_mm']+=length;row['layers'][layer]=row['layers'].get(layer,0)+length
            assert pcb.ToMM(track.GetWidth())>=.25
    for row in totals.values():
        row['length_mm']=round(row['length_mm'],6);row['layers']={k:round(v,6) for k,v in row['layers'].items()}
    result=dict(pad_net_assignments_identical=True,components_identical=True,components=len(components),pads=len(actual),
        board_size_mm=[60,70],net_geometry=dict(sorted(totals.items())),segments=sum(r['segments'] for r in totals.values()),
        vias=sum(r['via_count'] for r in totals.values()),length_mm=sum(r['length_mm'] for r in totals.values()),
        scope='Native PCB geometry after SES import; per-net sums are not longest-path delays. Two ground zones require filling and DRC.',
        electrical_qualification=False,fabrication_ready=False)
    (HERE/'routing.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Imported route:',result['segments'],'segments,',result['vias'],'vias;',len(actual),'pad assignments unchanged')


if __name__=='__main__':main()
