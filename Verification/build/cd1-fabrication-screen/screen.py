"""Create a supplier-rule screening copy of P2, then export offline CAM.

Run with KiCad bundled Python. This is not a fabrication release.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'sources/CD1-P2-routed.kicad_pcb'
BOARD=HERE/'CD1-P2-SCREEN-NOT-FOR-FAB.kicad_pcb'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]


def command(args,log):
    run=subprocess.run(args,capture_output=True,text=True)
    (HERE/log).write_text(run.stdout+run.stderr)
    assert run.returncode in (0,5) if 'drc' in args else run.returncode==0,(args,run.stdout,run.stderr)
    return run.returncode


def main():
    original_hash=sha(SOURCE)
    spec=importlib.util.spec_from_file_location('p2',HERE.parent/'cd1-stitching/generate.py')
    p2=importlib.util.module_from_spec(spec);spec.loader.exec_module(p2)
    original=pcb.LoadBoard(str(SOURCE))
    board=pcb.LoadBoard(str(SOURCE))
    # Mask change is explicit and confined to this screening copy.
    board.GetDesignSettings().m_SolderMaskExpansion=pcb.FromMM(.0508)
    pcb.SaveBoard(str(BOARD),board)
    project=json.loads(SOURCE.with_suffix('.kicad_pro').read_text())
    rules=project['board']['design_settings']['rules']
    minima=dict(min_clearance=.25,min_connection=.1524,min_copper_edge_clearance=.5,
                min_hole_clearance=.25,min_hole_to_hole=.25,min_through_hole_diameter=.3,
                min_track_width=.25,min_via_annular_width=.2,min_via_diameter=.508,
                min_text_height=.8,min_text_thickness=.127)
    changes=[]
    for key,minimum in minima.items():
        old=rules[key];rules[key]=max(old,minimum)
        changes.append(dict(setting=key,before=old,after=rules[key]))
    BOARD.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    # Original custom rules remain byte-for-byte prefixes, preserving stricter values.
    BOARD.with_suffix('.kicad_dru').write_text(SOURCE.with_suffix('.kicad_dru').read_text()+
        '(rule "Screen connection width" (constraint connection_width (min 0.1524mm)))\n'+
        '(rule "Screen via diameter" (constraint via_diameter (min 0.508mm)))\n'+
        '(rule "Screen drill" (constraint hole_size (min 0.3mm)))\n')
    stored=pcb.LoadBoard(str(BOARD))
    assert p2.pad_signatures(stored)==p2.pad_signatures(original)
    assert {t.m_Uuid.AsString():p2.track_signature(t) for t in stored.GetTracks()}=={
        t.m_Uuid.AsString():p2.track_signature(t) for t in original.GetTracks()}
    assert stored.GetDesignSettings().m_SolderMaskExpansion==pcb.FromMM(.0508)
    code=command(['kicad-cli','pcb','drc',str(BOARD),'--format','json','--output',str(HERE/'screen-drc.json'),
                  '--severity-all','--refill-zones','--exit-code-violations'],'screen-drc.log')
    drc=json.loads((HERE/'screen-drc.json').read_text())
    assert not any(v['type']=='lib_footprint_issues' for v in drc['violations']), drc
    cam=HERE/'cam-preview';cam.mkdir(exist_ok=True)
    commands=[['kicad-cli','pcb','export','gerbers',str(BOARD),'--output',str(cam),
               '--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts','--precision','6','--check-zones'],
              ['kicad-cli','pcb','export','drill',str(BOARD),'--output',str(cam),'--format','excellon',
               '--drill-origin','absolute','--excellon-zeros-format','decimal','--excellon-units','mm',
               '--excellon-separate-th','--generate-report','--report-path',str(HERE/'drill-report.txt')]]
    for i,args in enumerate(commands):command(args,'cam-export-%s.log'%i)
    drills=[];pads=[]
    for f in stored.GetFootprints():
        for p in f.Pads():
            assert p.GetAttribute()==pcb.PAD_ATTRIB_PTH and p.GetDrillSize().x==p.GetDrillSize().y
            drills.append(dict(id=f.GetReference()+'.'+p.GetNumber(),position=xy(p.GetPosition()),
                               diameter_mm=pcb.ToMM(p.GetDrillSize().x),plated=True))
            pads.append(dict(id=f.GetReference()+'.'+p.GetNumber(),position=xy(p.GetPosition()),
                             size_mm=xy(p.GetSize()),shape=int(p.GetShape())))
    for t in stored.GetTracks():
        if isinstance(t,pcb.PCB_VIA):
            drills.append(dict(id=t.m_Uuid.AsString(),position=xy(t.GetPosition()),diameter_mm=pcb.ToMM(t.GetDrillValue()),plated=True))
    edges=[]
    for item in stored.GetDrawings():
        if item.GetLayer()==pcb.Edge_Cuts:
            assert isinstance(item,pcb.PCB_SHAPE) and item.GetShape()==pcb.SHAPE_T_SEGMENT
            edges.append(dict(start=xy(item.GetStart()),end=xy(item.GetEnd()),width_mm=pcb.ToMM(item.GetWidth())))
    assert len(drills)==99 and len(edges)==4 and len(pads)==90
    (HERE/'native-cam-geometry.json').write_text(json.dumps(dict(board_sha256=sha(BOARD),drills=drills,
        outline=edges,pads=pads,mask_expansion_mm=.0508),indent=2)+'\n')
    assert sha(SOURCE)==original_hash
    result=dict(source_sha256=original_hash,screen_sha256=sha(BOARD),kicad_version=pcb.Version(),
        pad_and_track_parity=True,pads=90,tracks=185,vias=9,mask_expansion_before_mm=0,
        mask_expansion_after_mm=.0508,rule_changes=changes,drc_exit=code,
        drc_violations=len(drc['violations']),unconnected_items=len(drc['unconnected_items']),
        ignored_checks=drc['ignored_checks'],cam_commands=commands,
        scope='Configured rule screen and offline CAM exports. No supplier preview, fit, electrical or fabrication acceptance.',
        fabrication_ready=False)
    (HERE/'screen.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Screen copy: %s DRC violations, %s unconnected; 99 drills exported'%(result['drc_violations'],result['unconnected_items']))


if __name__=='__main__':main()
