"""P3 isolated nominal capacitor placement; retain all original signal copper."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import subprocess
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
BOARD=HERE/'CD1-P3-decoupling.kicad_pcb'
SOURCE=HERE/'sources/CD1-P2-routed.kicad_pcb'


def point(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(p):return [pcb.ToMM(p.x),pcb.ToMM(p.y)]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def padmap(b):return {(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints() for p in f.Pads()}


def main():
    spec=importlib.util.spec_from_file_location('p2',HERE.parent/'cd1-stitching/generate.py')
    p2=importlib.util.module_from_spec(spec);spec.loader.exec_module(p2)
    before=sha(SOURCE);old=pcb.LoadBoard(str(SOURCE));b=pcb.LoadBoard(str(SOURCE))
    originals={t.m_Uuid.AsString():p2.track_signature(t) for t in old.GetTracks()}
    oldpads=padmap(old);caps=[];newtracks=[];newvias=[]
    lib=HERE/'footprints/CD1-Experiment.pretty'
    for i in range(1,4):
        ref='C'+str(i);ic='U'+str(i)
        previous=next(f for f in b.GetFootprints() if f.GetReference()==ref)
        cap=pcb.FootprintLoad(str(lib),'C315C104K5R5TA');assert cap is not None
        cap.SetReference(ref);cap.SetValue('100nF C315C104K5R5TA');cap.SetFPID(pcb.LIB_ID('CD1-Experiment','C315C104K5R5TA'))
        vcc=oldpads[ic,'20'];x,y=xy(vcc.GetPosition())
        # U3's first right-hand placement intersects an existing ground track
        # and ME1_PH2. Move only its capacitor upward, retaining signal copper.
        dy=-2.5 if i==3 else 0
        cap.SetOrientationDegrees(-90);cap.SetPosition(point(x+3,y+dy));cap.Value().SetVisible(False)
        cap.Reference().SetTextSize(point(.8,.8));cap.Reference().SetTextThickness(pcb.FromMM(.15))
        cap.Reference().SetTextAngle(pcb.EDA_ANGLE(0,pcb.DEGREES_T))
        cap.Reference().SetPosition(point(x+5.6,y+dy+1.27))
        b.Add(cap)
        for p in cap.Pads():p.SetNet(b.FindNet('/5V' if p.GetNumber()=='1' else '/GND'))
        b.Remove(previous)
        # Old C1/C2 VCC barrels join front and back backbone tracks. Preserve
        # that function explicitly when their component pads move.
        if i in (1,2):
            v=pcb.PCB_VIA(b);v.SetPosition(oldpads[ref,'1'].GetPosition())
            v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
            v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetNet(b.FindNet('/5V'));b.Add(v)
            newvias.append(dict(id=v.m_Uuid.AsString(),position=xy(v.GetPosition()),net='/5V'))
        p=next(p for p in cap.Pads() if p.GetNumber()=='1')
        t=pcb.PCB_TRACK(b);t.SetStart(vcc.GetPosition());t.SetEnd(p.GetPosition());t.SetLayer(pcb.F_Cu)
        t.SetWidth(pcb.FromMM(.5));t.SetNet(b.FindNet('/5V'));b.Add(t)
        newtracks.append(dict(id=t.m_Uuid.AsString(),start=xy(t.GetStart()),end=xy(t.GetEnd()),width_mm=.5))
        caps.append(dict(ref=ref,ic=ic,vcc_pin='20',ground_pin='10',
            pads=[dict(pin=p.GetNumber(),position=xy(p.GetPosition()),net=p.GetNetname()) for p in cap.Pads()]))
    b.GetDesignSettings().m_SolderMaskExpansion=pcb.FromMM(.0508)
    for drawing in b.GetDrawings():
        if isinstance(drawing,pcb.PCB_TEXT) and drawing.GetText()=='DM-02 CD1-P2':drawing.SetText('DM-02 CD1-P3')
    b.BuildConnectivity();pcb.ZONE_FILLER(b).Fill(b.Zones());pcb.SaveBoard(str(BOARD),b)
    for ext in ('.kicad_pro','.kicad_dru'):shutil.copyfile(HERE/('sources/screen'+ext),BOARD.with_suffix(ext))
    # This file only resolves the experiment's custom footprint. Standard
    # footprints are already embedded and globally configured in KiCad.
    (HERE/'fp-lib-table').write_text('(fp_lib_table\n (lib (name "CD1-Experiment")(type "KiCad")(uri "${KIPRJMOD}/footprints/CD1-Experiment.pretty")(options "")(descr "Nominal capacitor experiment"))\n)\n')
    stored=pcb.LoadBoard(str(BOARD));actual=padmap(stored)
    expected={(p.attrib['ref'],p.attrib['pin']):n.attrib['name'] for n in ET.parse(HERE/'sources/source.xml').findall('./nets/net') for p in n.findall('node')}
    assert {key:p.GetNetname() for key,p in actual.items()}==expected
    new={t.m_Uuid.AsString():p2.track_signature(t) for t in stored.GetTracks()}
    assert all(new[k]==v for k,v in originals.items())
    assert len(new)==len(originals)+5
    assert {k:v for k,v in p2.pad_signatures(old).items() if not k[0].startswith('C')}=={
        k:v for k,v in p2.pad_signatures(stored).items() if not k[0].startswith('C')}
    run=subprocess.run(['kicad-cli','pcb','drc',str(BOARD),'--format','json','--output',str(HERE/'drc.json'),
                        '--severity-all','--refill-zones','--exit-code-violations'],capture_output=True,text=True)
    (HERE/'drc.log').write_text(run.stdout+run.stderr)
    assert run.returncode in (0,5),(run.stdout,run.stderr)
    drc=json.loads((HERE/'drc.json').read_text())
    result=dict(source_sha256=before,board_sha256=sha(BOARD),capacitors=caps,added_tracks=newtracks,
        added_power_vias=newvias,original_tracks_and_vias_preserved=len(originals),noncapacitor_pads_preserved=84,
        native_xml_pad_net_parity=True,drc_exit=run.returncode,violations=len(drc['violations']),
        unconnected=len(drc['unconnected_items']),fabrication_ready=False)
    assert sha(SOURCE)==before
    (HERE/'generation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('P3: all original copper tracks/vias preserved;',len(drc['violations']),'DRC violations;',len(drc['unconnected_items']),'unconnected')


if __name__=='__main__':main()
