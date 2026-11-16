"""Fail-closed RR1 replay from native MD1 inventory and immutable event logs."""
import csv
import json
import re
from .common import ROOT,VROOT,BUILD,digest,write_json
from . import release_requirements as rr,release_sim as sim,release_measurements as measurements
from . import mar_distribution_evidence as mde

LOCK=VROOT/'release-evidence.json'
PREFIX='cp1-release/'
ACCEPTED='iteration-2'
BOOT_CASES={'boot-guarded-max':('guarded-max',10,False),'boot-zero':('zero',10,False),
    'boot-mixed2':('mixed2',10,False),'boot-mixed3':('mixed3',10,False),
    'boot-DATA-always-driven':('guarded-max',10,True),'boot-late-release':('guarded-max',5000,False)}
SOURCES=sim.SOURCES+['Verification/dm02/release_evidence.py','Verification/dm02/release_measurements.py']
require=rr.require


def canonical_hdl(text):
    # Archived iterations used a set for this declaration only. Net assignments
    # and every delay/expression must still match exactly; new generation sorts it.
    return re.sub(r'^wire (n\d+(?:,n\d+)*);$',
                  lambda m:'wire '+','.join(sorted(m[1].split(',')))+';',text,flags=re.M)


def opposing_turnovers(path):
    """Count changes of bus ownership once, excluding repeated same-side activity."""
    owner=None;prev={'ram':False,'writer':False};last_off={'ram':None,'writer':None}
    gaps={'read_to_write':[],'write_to_read':[]}
    with path.open() as source:
        for row in csv.DictReader(source):
            if any(row[k] not in ('0','1') for k in ('ram_oe_n','ram_we_n','writer_oe_n')):continue
            t=float(row['time_ns']);state={'ram':row['ram_oe_n']=='0' and row['ram_we_n']=='1','writer':row['writer_oe_n']=='0'}
            for key in state:
                if prev[key] and not state[key]:last_off[key]=t
            for key,other,direction in [('ram','writer','write_to_read'),('writer','ram','read_to_write')]:
                if state[key] and not prev[key]:
                    if owner==other and last_off[other] is not None:gaps[direction].append(t-last_off[other])
                    owner=key
            prev=state
    return {key:dict(count=len(v),minimum_requested_gap_ns=min(v) if v else None) for key,v in gaps.items()}


def model_review(build=BUILD):
    folder=build/'cp1-mar-distribution/simulation-1/boot-guarded-max'
    memory=(folder/'ME1.sv').read_text();support=(folder/'support.sv').read_text();bf=(folder/'BF1.sv').read_text()
    require('cp_sram #(15,10,15,12,9,7) U2 (' in memory,'RR1 instantiated SRAM changed')
    actual=support[support.index('module cp_sram '):]
    for text in ('#(reading ? TACC : TDIS);','if(generation==token) value=reading ? memory[a] : 8\'bz;',
                 'if(selected && !oe_n && we_n) value=8\'bx;',
                 'if(!oe_n) $fatal(1,"ME1 SRAM OE active during write");'):
        require(text in actual,'RR1 cp_sram behavior changed')
    require(re.search(r'cp_sram #[^\n]+,n\[132\],n\[133\],',memory),'RR1 OE/WE probe binding changed')
    require(len(re.findall(r'bufif0 #[^\n]+ U4_\d+ \([^\n]+,n\[140\]\);',memory))==8,'RR1 writer probe binding changed')
    require(len(re.findall(r'bufif0 #[^\n]+ U105_\d+ \([^\n]+,n\[69\]\);',bf))==8,'RR1 DATA probe binding changed')
    return dict(instantiated_module='cp_sram',unused_local_module='me_sram',parameters_ns=dict(TACC=15,TDIS=10,TWC=15,TAW=12,TWP=9,TDW=7),
        findings=[
            'cp_sram in support.sv is instantiated; the me_sram module text in ME1.sv is unused.',
            'One generic TDIS applies to OE, WE, CE and address-triggered resolution. It does not implement separate 9 ns OE / 8 ns WE / 10 ns CE release bounds.',
            'Read request immediately drives X, then resolves after TACC; this is not a characterized low-Z minimum.',
            'Generation-token cancellation and address changes can restart the generic release task; source-level model timing is not a physical release guarantee.',
            'The independent RR1 activity monitor uses zero activation delay and separate SRAM/writer release delays, detecting overlap even when data matches.',
            'A positive maximum release time cannot establish minimum valid-data hold. SRAM/U9009 share OE; invalid SRAM data may reach the mux and still-enabled source buffer before the latter reaches high-Z.'
        ],physical_qualification=False)


def summary(build=BUILD):
    folder=build/PREFIX/ACCEPTED;graph=rr.Graph(json.loads((build/'cp1-mar-distribution/final/loads.json').read_text()))
    audit=graph.audit();boots={}
    for name in BOOT_CASES:
        result=json.loads((folder/name/'result.json').read_text())
        boots[name]=dict(expectation_met=result['expectation_met'],opposing_turnovers=opposing_turnovers(folder/name/'release-events.csv'),
                         expected=result['expected'],physical_qualification=False)
    return dict(revision='CP1-RR1',candidate='CP1-MD1',audit=audit,model_review=model_review(build),boots=boots,
        short_cases=len(sim.CASES),short_passes=sum('expected' not in c for c in sim.CASES.values()),
        short_faults=sum('expected' in c for c in sim.CASES.values()),native_faults=rr.mutations(graph.inventory),
        measurement_plan=measurements.plan(audit),physical_qualification=False,promoted_into_R2=False)


def verify(lock,build=BUILD):
    require(lock.get('revision')=='CP1-RR1' and lock.get('physical_qualification') is False,'Invalid RR1 scope')
    require(set(SOURCES)<=lock['source_hashes'].keys(),'Missing RR1 source')
    base=PREFIX+ACCEPTED+'/'
    required={PREFIX+'summary.json',base+'audit.json',base+'native-faults.json',base+'short-matrix.json',base+'boot-matrix.json'}
    for name in (*sim.CASES,*BOOT_CASES):
        required|={base+name+'/'+n for n in ('result.json','simulation.log','compile.log','release-events.csv','release_watch.sv','tb.sv')}
    required|={base+name+'/controls.sv' for name in sim.CASES}
    require(required<=lock['artifacts'].keys(),'Missing RR1 artifact')
    for root,hashes in ((ROOT,lock['source_hashes']),(build,lock['artifacts'])):
        for name,sha in hashes.items():
            path=(root/name).resolve();require(path.is_relative_to(root.resolve()),'RR1 path escape')
            require(path.is_file() and digest(path)==sha,'Changed RR1 evidence: '+name)
    mde.load(build);folder=build/base
    graph=rr.Graph(json.loads((build/'cp1-mar-distribution/final/loads.json').read_text()))
    # The iteration audit is historical. summary.json regenerates the final,
    # expanded address and neighbouring SOURCE3 control paths from the same pins.
    require(rr.mutations(graph.inventory)==json.loads((folder/'native-faults.json').read_text()),'RR1 mutation replay differs')
    short_matrix=json.loads((folder/'short-matrix.json').read_text());boot_matrix=json.loads((folder/'boot-matrix.json').read_text())
    require(set(short_matrix)==set(sim.CASES) and set(boot_matrix)==set(BOOT_CASES),'Incomplete RR1 matrix')
    for name in (*sim.CASES,*BOOT_CASES):
        run=folder/name;r=json.loads((run/'result.json').read_text());log=(run/'simulation.log').read_text()
        require(r==(short_matrix if name in sim.CASES else boot_matrix)[name],'RR1 result matrix differs')
        expected=sim.CASES[name].get('expected','PASS RR1') if name in sim.CASES else ('RR1 drive overlap' if name=='boot-late-release' else 'PASS TX1 CPU received=5')
        require(r['expected']==expected and r['expectation_met'] and r['physical_qualification'] is False,'Invalid RR1 result')
        require(expected in log and (r['exit_code']==0)==expected.startswith('PASS'),'Missing RR1 oracle/fault')
        require(r['events']==sim.event_summary(run/'release-events.csv'),'RR1 recorded events differ')
        for source,sha in r['source_hashes'].items():
            require(digest(folder/'source-snapshot'/source)==sha,'RR1 run source snapshot differs')
        for file,sha in r['model_hashes'].items():require(digest(run/file)==sha,'RR1 model changed')
        require((run/'release_watch.sv').read_text()==(VROOT/'hdl/release_watch.sv').read_text(),'RR1 monitor differs')
        if name in sim.CASES:
            case=sim.CASES[name]
            require(canonical_hdl((run/'controls.sv').read_text())==canonical_hdl(graph.hdl(case['profile'])),'RR1 native-control regeneration differs')
            require((run/'tb.sv').read_text()==sim.fixture(graph,case),'RR1 short fixture differs')
            if expected.startswith('PASS'):
                require(r['events']['reset_assertions']==2 and r['events']['write_pulses']==2,'RR1 reset/write coverage missing')
        else:
            case,release,retain=BOOT_CASES[name]
            require(set(r['input_hashes'])<=lock['artifacts'].keys(),'Missing RR1 original boot dependency')
            for source,sha in r['input_hashes'].items():
                require(digest(build/source)==sha,'RR1 original boot changed')
                file=source.rsplit('/',1)[1];text=None
                if file=='tb.sv':text=(build/source).read_text().replace('endmodule',sim.boot_probe(release)+'\nendmodule')
                elif file=='BF1.sv' and retain:
                    text=(build/source).read_text()
                    text=re.sub(r'(bufif0 #\([^\n]+\) U105_\d+ \([^\n]+),n\[69\]\);',r"\1,1'b0);",text)
                    text=re.sub(r'(wire cp_active_U105;assign #\([^\n]+\) cp_active_U105=)~n\[69\];',r"\g<1>1'b1;",text)
                if text is None:require(digest(run/file)==sha,'RR1 unrelated boot input changed')
                else:require((run/file).read_text()==text,'RR1 boot transformation differs')
            if expected.startswith('PASS'):
                require('PASS TB1 ROM reconstruction bytes=160 writes=160 pc=4000' in log,'RR1 boot reconstruction absent')
                require(not sum(map(int,re.findall(r'TIMING_SUMMARY .*violations=(\d+)',log))),'RR1 boot timing violation')
    actual=summary(build);require(actual==json.loads((build/PREFIX/'summary.json').read_text()),'RR1 summary replay differs')
    return actual


def load(build=BUILD):
    lock=json.loads(LOCK.read_text());return lock,verify(lock,build)
