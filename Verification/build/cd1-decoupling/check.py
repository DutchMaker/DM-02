"""Exercise the new capacitor feeds and retained power-backbone transitions."""
from pathlib import Path
import copy
import hashlib
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import pcbnew as pcb

HERE=Path(__file__).resolve().parent
BOARD=HERE/'CD1-P3-decoupling.kicad_pcb'


def check_geometry(data,original,plan):
    xml=ET.parse(HERE/'sources/source.xml')
    expected={(p.attrib['ref'],p.attrib['pin']):n.attrib['name'] for n in xml.findall('./nets/net') for p in n.findall('node')}
    assert {(p['ref'],p['pin']):p['net'] for p in data['pads']}==expected,'native XML pin/net identity'
    tracks={t['id']:t for t in data['tracks']}
    for old in original['tracks']:
        assert tracks[old['id']]==old,'original track changed'
    vias={v['id']:v for v in data['vias']}
    for old in original['vias']:assert vias[old['id']]==old,'original via changed'
    for feed in plan['added_tracks']:
        assert feed['id'] in tracks,'missing local capacitor feed'
        t=tracks[feed['id']]
        assert t['net']=='/5V' and t['width_mm']==.5 and t['start']==feed['start'] and t['end']==feed['end'],'local capacitor feed'
    for via in plan['added_power_vias']:
        assert via['id'] in vias,'missing backbone via'
        v=vias[via['id']]
        assert v['net']=='/5V' and v['position']==via['position'] and v['drill_mm']==.4 and v['diameter_mm']==.8,'backbone via'


def main():
    original=json.loads((HERE/'sources/p2-geometry.json').read_text())
    data=json.loads((HERE/'geometry.json').read_text());plan=json.loads((HERE/'generation.json').read_text())
    check_geometry(data,original,plan)
    folder=HERE/'faults';folder.mkdir(exist_ok=True)
    faults=[]
    for kind,rows in [('feed',plan['added_tracks']),('backbone-via',plan['added_power_vias'])]:
        for i,row in enumerate(rows):
            path=folder/f'missing-{kind}-{i+1}.kicad_pcb'
            # KiCad's embedded SWIG bindings failed during repeated board
            # destruction/reload in one interpreter. Isolate each native edit.
            worker=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--make-fault',row['id'],str(path)],capture_output=True,text=True)
            path.with_suffix('.generation.log').write_text(worker.stdout+worker.stderr)
            assert worker.returncode==0,(path,worker.stdout,worker.stderr)
            for suffix in ('.kicad_pro','.kicad_dru'):shutil.copyfile(BOARD.with_suffix(suffix),path.with_suffix(suffix))
            # Custom library path must resolve from the mutant directory too.
            (folder/'fp-lib-table').write_text((HERE/'fp-lib-table').read_text().replace('${KIPRJMOD}/footprints','${KIPRJMOD}/../footprints'))
            result=subprocess.run(['kicad-cli','pcb','drc',str(path),'--format','json','--output',str(path.with_suffix('.json')),
                '--severity-all','--refill-zones','--exit-code-violations'],capture_output=True,text=True)
            path.with_suffix('.log').write_text(result.stdout+result.stderr)
            drc=json.loads(path.with_suffix('.json').read_text())
            # C2 also touches the retained backside supply backbone. Removing
            # its wide front feed preserves DC connectivity, so DRC alone must
            # not be used to enforce the local-feed intent.
            redundant=(kind=='feed' and i==1)
            if redundant:assert result.returncode==0 and not drc['unconnected_items'] and not drc['violations']
            else:assert result.returncode==5 and drc['unconnected_items'],(path.name,result.stdout,result.stderr)
            assert row['id'] not in path.read_text(), 'removed UUID survived serialized mutation'
            bad=copy.deepcopy(data)
            key='tracks' if kind=='feed' else 'vias'
            bad[key]=[t for t in bad[key] if t['id']!=row['id']]
            try:check_geometry(bad,original,plan)
            except AssertionError as error:diagnostic=str(error)
            else:raise AssertionError('Missing feature escaped explicit intent check')
            faults.append(dict(fault=path.stem,detected=True,intent_diagnostic=diagnostic,
                drc_detected=bool(drc['unconnected_items'] or drc['violations']),
                alternative_dc_path=redundant,unconnected_items=len(drc['unconnected_items']),
                violation_types=sorted({v['type'] for v in drc['violations']})))
    geometry_faults=[]
    for fault in ('capacitor-ground-to-5v','narrow-feed','signal-endpoint-moved'):
        bad=copy.deepcopy(data)
        if fault=='capacitor-ground-to-5v':next(p for p in bad['pads'] if p['ref']=='C1' and p['pin']=='2')['net']='/5V'
        elif fault=='narrow-feed':next(t for t in bad['tracks'] if t['id']==plan['added_tracks'][0]['id'])['width_mm']=.25
        else:next(t for t in bad['tracks'] if t['net'].startswith('/ROOT'))['start'][0]+=.1
        try:check_geometry(bad,original,plan)
        except AssertionError as error:geometry_faults.append(dict(fault=fault,detected=True,diagnostic=str(error)))
        else:raise AssertionError('Geometry fault escaped '+fault)
    (HERE/'checks.json').write_text(json.dumps(dict(passed=True,board_sha256=hashlib.sha256(BOARD.read_bytes()).hexdigest(),native_faults=faults,geometry_faults=geometry_faults),indent=2)+'\n')
    print('Five saved native omissions detected by intent; four detected by DRC; three geometry faults detected')


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--make-fault':
        b=pcb.LoadBoard(str(BOARD))
        target=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==sys.argv[2])
        b.Remove(target);pcb.SaveBoard(sys.argv[3],b)
    else:main()
