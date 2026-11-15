"""Place a CD1 routing trial from its native KiCad XML netlist.

Use KiCad's bundled Python (pcbnew). This is a layout experiment, not a
fabrication release: exact connectors/passives and electrical extraction open.
"""
from pathlib import Path
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
LIBRARY=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
SOURCE=ROOT/'Verification/build/distribution/native/CD1/Clock-Distribution.xml'
SCHEMATIC=ROOT/'Circuits/KiCad/Distribution/candidates/Clock-Distribution.sch'
NATIVE=SOURCE.with_suffix('.kicad_sch')
PLACEMENT={'J1':(24,43),'U1':(33,37),'U2':(53,28),'U3':(53,61),
           'J2':(74,28),'C1':(40.62,33),'C2':(60.62,24),'C3':(60.62,57)}


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def point(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))


def generate():
    comparison=json.loads(SOURCE.with_name('comparison.json').read_text())
    assert comparison['status']=='pass' and comparison['source_hash']==digest(SCHEMATIC)
    tree=ET.parse(SOURCE).getroot();board=pcb.BOARD();board.SetCopperLayerCount(2)
    board.SetFileName(str(HERE/'CD1-P0.kicad_pcb'))
    default=board.GetAllNetClasses()['Default']
    default.SetClearance(pcb.FromMM(.25));default.SetTrackWidth(pcb.FromMM(.25))
    default.SetViaDiameter(pcb.FromMM(.8));default.SetViaDrill(pcb.FromMM(.4))
    settings=board.GetDesignSettings();settings.m_MinClearance=pcb.FromMM(.25)
    settings.m_TrackMinWidth=pcb.FromMM(.25);settings.m_CopperEdgeClearance=pcb.FromMM(.5)
    nets={};expected={};parts={};hashes={}
    for node in tree.findall('./nets/net'):
        name=node.attrib['name'];net=pcb.NETINFO_ITEM(board,name);board.Add(net);nets[name]=net
        for pin in node.findall('node'):
            key=(pin.attrib['ref'],pin.attrib['pin']);assert key not in expected
            expected[key]=name
    for component in tree.findall('./components/comp'):
        ref=component.attrib['ref'];identity=component.findtext('footprint');library,name=identity.split(':')
        path=LIBRARY/(library+'.pretty')/(name+'.kicad_mod');hashes[identity]=digest(path)
        fp=pcb.FootprintLoad(str(path.parent),name);assert fp is not None
        fp.SetFPID(pcb.LIB_ID(library,name));fp.SetReference(ref);fp.SetValue(component.findtext('value'))
        fp.SetPosition(point(*PLACEMENT[ref]));fp.Value().SetVisible(False)
        fp.Reference().SetTextSize(point(1,1));fp.Reference().SetTextThickness(pcb.FromMM(.15))
        board.Add(fp);parts[ref]=fp
        for pad in fp.Pads():
            key=(ref,pad.GetNumber());assert key in expected,key
            pad.SetNet(nets[expected[key]])
        target=HERE/'footprints'/(library+'.pretty')/path.name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,target)
    assert set(parts)==set(PLACEMENT)
    actual={(fp.GetReference(),pad.GetNumber()):pad.GetNetname() for fp in board.GetFootprints() for pad in fp.Pads()}
    assert actual==expected
    for start,end in [((20,20),(80,20)),((80,20),(80,90)),((80,90),(20,90)),((20,90),(20,20))]:
        line=pcb.PCB_SHAPE();line.SetShape(pcb.SHAPE_T_SEGMENT);line.SetStart(point(*start));line.SetEnd(point(*end))
        line.SetLayer(pcb.Edge_Cuts);line.SetWidth(pcb.FromMM(.05));board.Add(line)
    for text,xy in [('DM-02 CD1-P0',(38,24)),('ROUTING TRIAL',(38,27)),('NOT FOR FABRICATION',(44,87))]:
        label=pcb.PCB_TEXT(board);label.SetText(text);label.SetPosition(point(*xy));label.SetLayer(pcb.F_SilkS)
        label.SetTextSize(point(1,1));label.SetTextThickness(pcb.FromMM(.15));board.Add(label)
    board.BuildConnectivity();pcb.SaveBoard(str(HERE/'CD1-P0.kicad_pcb'),board)
    assert pcb.ExportSpecctraDSN(board,str(HERE/'CD1-P0.dsn'))
    shutil.copyfile(SOURCE,HERE/'source.xml');shutil.copyfile(NATIVE,HERE/'source.kicad_sch')
    (HERE/'fp-lib-table').write_text('(fp_lib_table\n'+''.join(
        f' (lib (name "{name}")(type "KiCad")(uri "{LIBRARY/(name+".pretty")}")(options "")(descr ""))\n'
        for name in sorted({key.split(':')[0] for key in hashes}))+')\n')
    result=dict(passed=True,scope='Unrouted placement and exact pad/net assignment only; no release approval.',
        source_sha256=digest(SCHEMATIC),native_xml_sha256=digest(SOURCE),native_schematic_sha256=digest(NATIVE),
        footprint_hashes=hashes,components=len(parts),pads=len(actual),nets=len(nets),
        placement_mm=PLACEMENT,board_size_mm=[60,70],layers=2,
        routing_rules=dict(track_width_mm=.25,clearance_mm=.25,via_diameter_mm=.8,via_drill_mm=.4,copper_edge_mm=.5),
        open=['Exact connectors, gender and mating board geometry','Exact capacitors and assembly fit',
              'Power distribution, decoupling-loop inductance and return paths','Trace/connector capacitance and clock slew/skew',
              'Mechanical mounting and independent electrical review'])
    (HERE/'placement.json').write_text(json.dumps(result,indent=2)+'\n')
    print('CD1 trial:',len(parts),'footprints,',len(actual),'pads,',len(nets),'native nets; exact pad assignments pass')


if __name__=='__main__':generate()
