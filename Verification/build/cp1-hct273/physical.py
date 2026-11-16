"""Package pads, owned-memory pin contracts and bounded HC receiver review."""
from pathlib import Path
from collections import defaultdict
import importlib.util,json,shutil
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('cp_run',HERE/'run.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
from dm02.common import digest,write_json
from dm02.sexpr import parse
from dm02.legacy import read_sheet,connectivity
from dm02.compact_hardware import Circuit
from designs.compact_candidate import DEST

def main():
    packages=json.loads((HERE/'packages.json').read_text());footprints={}
    libraries=Path.home()/'Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints'
    for name in sorted({p['footprint'] for p in packages}):
        lib,fp=name.split(':');source=libraries/(lib+'.pretty')/(fp+'.kicad_mod')
        target=HERE/'footprints'/(lib+'.pretty')/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        pads=[x for x in parse(target.read_text()) if isinstance(x,list) and x and x[0]=='pad']
        assert pads and all(p[2]=='thru_hole' for p in pads),name
        footprints[name]=dict(sha256=digest(target),pads=sorted({p[1] for p in pads}),through_hole=True)
    for board in sorted({p['board'] for p in packages}):
        sheet=read_sheet(DEST/(board+'.sch'));pins=defaultdict(set)
        for c in sheet['components']:pins[c['ref']].update(p['number'] for p in c['pins'])
        for p in (x for x in packages if x['board']==board):
            assert pins[p['ref']]==set(footprints[p['footprint']]['pads']),(board,p['ref'],pins[p['ref']],p['footprint'])
    # Datasheet table transcription is separate from the drawing pin-map code.
    expected={
      ('CW1','U1'):{'1':'VPP','2':'~E','3':'Q15','10':'Q8','11':'VSS','12':'Q7','19':'Q0','20':'~G','21':'A0','29':'A8','30':'VSS','31':'A9','37':'A15','38':'NC','39':'~P','40':'VCC'},
      ('ME1','U2'):{'1':'NC','2':'NC','3':'A14','4':'A12','12':'A0','13':'DQ0','16':'GND','21':'DQ7','22':'~CE1','23':'A10','24':'~OE','25':'A11','26':'A9','27':'A8','28':'A13','29':'~WE','30':'CE2','31':'A15','32':'VCC'},
      ('SP1','U3'):{'1':'D1','2':'Q1','3':'Q0','4':'~CE','5':'DOWN','6':'Q2','7':'Q3','8':'GND','9':'D3','10':'D2','11':'~LOAD','12':'TC','13':'~RCO','14':'CLK','15':'D0','16':'VCC'}}
    contracts=[]
    for (board,ref),mapping in expected.items():
        c=Circuit(board);part=c.components[ref][0];pins={p['number']:p['name'] for p in part['pins']}
        assert all(pins[p]==name for p,name in mapping.items()),(board,ref,pins)
        for pin,name in mapping.items():
            if name=='NC':assert c.nets[c.nodes[ref,pin]]['nodes']==[[ref,pin]]
        contracts.append(dict(board=board,ref=ref,part=part['value'],pins_checked=len(mapping),passed=True))
    loads=json.loads((HERE/'loads.json').read_text());hc=[]
    for row in loads:
        receivers=[x for x in row['receivers'] if x['part']=='SN74HC377N']
        for receiver in receivers:
            assert len(row['drivers'])==1,(receiver,row['drivers'])
            driver=row['drivers'][0];name=driver['part']
            assert name.startswith(('SN74AHCT','SN74HCT574','SN74HCT245')),name
            voh=3.7 if name=='SN74HCT574N' else 3.84 if name=='SN74HCT245N' else 3.94
            hc.append(dict(receiver=receiver,driver=driver,vol_max_v=0.4,voh_min_v=voh,vih_min_v=3.15,vil_max_v=1.35,
                high_margin_v=voh-3.15,low_margin_v=1.35-0.4,conditions='Common 4.5 V DC table point; -40..85 C. Full-supply and dynamic thresholds remain unqualified.'))
    assert hc and all(x['high_margin_v']>0 and x['low_margin_v']>0 for x in hc)
    result=dict(passed=True,footprints=footprints,packages_checked=len(packages),memory_counter_pin_contracts=contracts,
        hc377_inputs=hc,physical_qualification=False,open_items=[
            'No guaranteed HCT245 IO capacitance; 10 pF per port is a stated allocation.',
            'HCT245 data/enable timing is taken at 150 pF; disable timing is only guaranteed at 50 pF.',
            'CD74HCT273E clock/clear delays have explicit SCHS174D bounds at 4.5 V, -40..85 C and 50 pF. Actual output loads and input edges remain unqualified.',
            'SRAM read table uses 30 pF; output release uses 5 pF. Actual DQ load and turnaround require qualification.',
            'HC377 DC compatibility checked at 4.5 V only; full-supply loaded edges remain open.',
            'MCP100-450D does not establish valid 4.75 V startup; the staged system retains an external qualified reset input.',
            'Oscillator startup, duty at receiver thresholds, power integrity, routing and external IO electronics remain open.',
            'Owned 191/245/574 manufacturer/suffix/counts and EPROM programmer/readback remain unresolved.'])
    write_json(HERE/'physical-review.json',result)
    print('Physical pad maps:',len(packages),'packages;',len(hc),'HC377 nonconstant inputs reviewed')
if __name__=='__main__':main()
