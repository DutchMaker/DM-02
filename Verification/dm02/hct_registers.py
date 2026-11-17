"""HR1: six resetless HCT377 substitutions, separate from accepted R2/HB1."""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
import argparse
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from .common import ROOT,VROOT,BUILD,command,digest,write_json
from . import hct_buffers as hb, hct_evidence as he, hct_preference as hp
from .legacy import read_sheet,connectivity
from .native_migrate import blocks
from .sexpr import parse,child,quote

STUDY=BUILD/'cp1-hct-registers'
CANONICAL=ROOT/'Circuits/KiCad/Integrated/candidates/HR1'
PART='CD74HCT377E'
TARGETS={'AL1':('U6','U7'),'RG1':('U3','U8','U13','U18')}
DPINS=[3,4,7,8,13,14,17,18]
QPINS=[2,5,6,9,12,15,16,19]
MODEL=VROOT/'hdl/hct377.sv'
require=hb.require
COMPACT='cp1-hct273/candidate/Verification/build/compact/'
NATIVE_FAULTS=('data-swap','clock-to-enable','wrong-part')


class Candidate(hb.Candidate):
    def __init__(self):
        super().__init__()
        self.targets={r:c for r,c in self.components.items()
            if c['board'] in TARGETS and c['source_reference'] in TARGETS[c['board']]}
        require(len(self.targets)==6,'HR1 target count')
        for c in self.targets.values():
            require(c['value']=='SN74HC377N','HR1 source identity')
            require({p['num']:p['type'] for p in c['pin_signature']}==hp.pin_roles('377'),'HR1 DIP pin roles')
            c['value']=PART

    def documents(self,fault=None):
        require(fault is None or fault in NATIVE_FAULTS,'Unknown HR1 native fault')
        docs=super().documents()
        for board in TARGETS:
            text=docs[board+'.kicad_sch']
            text=text.replace('SN74HC377N',PART)
            if board=='RG1' and fault:
                # Mutate the target's physical pin labels, not a behavioural model.
                out=[];locations={}
                for block in blocks(text):
                    if block.startswith('(symbol (lib_id '):
                        node=parse(block)
                        ref=next(p[2] for p in node if isinstance(p,list) and p[:2]==['property','Reference'])
                        if ref=='U6003':
                            if fault=='wrong-part':block=block.replace(PART,'SN74HC377N')
                            libid=child(node,'lib_id')[1];x,y=map(float,child(node,'at')[1:3])
                            library=next(b for b in blocks(text) if b.startswith('(lib_symbols'))
                            symbol=next(parse(b) for b in blocks(library) if b.startswith('(symbol ') and parse(b)[1]==libid)
                            for unit in symbol:
                                if not isinstance(unit,list) or unit[0]!='symbol':continue
                                for pin in unit:
                                    if isinstance(pin,list) and pin[0]=='pin':
                                        px,py=map(float,child(pin,'at')[1:3]);locations[child(pin,'number')[1]]=(round(x+px,6),round(y-py,6))
                    out.append(block)
                a,b=('3','4') if fault=='data-swap' else ('11','1')
                names={}
                for block in out:
                    if block.startswith('(global_label '):
                        n=parse(block);pos=tuple(map(float,child(n,'at')[1:3]))
                        for p in (a,b):
                            if pos==locations[p]:names[p]=n[1]
                require(len(names)==2,'HR1 mutation pin labels')
                if fault!='wrong-part':
                    out=[block.replace(quote(names[a]),quote(names[b]),1) if block.startswith('(global_label '+quote(names[a])+' ') and tuple(map(float,child(parse(block),'at')[1:3]))==locations[a]
                        else block.replace(quote(names[b]),quote(names[a]),1) if block.startswith('(global_label '+quote(names[b])+' ') and tuple(map(float,child(parse(block),'at')[1:3]))==locations[b] else block for block in out]
                text='(kicad_sch\n'+'\n'.join(out)+'\n)\n'
            docs[board+'.kicad_sch']=text
        return {n.replace('HB1.kicad_sch','HR1.kicad_sch'):t.replace('HB1','HR1') for n,t in docs.items()}

    def generate(self,folder,fault=None):
        folder=Path(folder);require(not folder.exists(),'Preserve HR1 native attempt');folder.mkdir(parents=True)
        for name,text in self.documents(fault).items():(folder/name).write_text(text)
        code,log=command(['kicad-cli','sch','export','netlist','--format','kicadxml','--output',folder/'HR1.xml',folder/'HR1.kicad_sch'])
        (folder/'export.log').write_text(log);require(code==0,'HR1 export failed: '+log)
        result=self.compare(folder/'HR1.xml');write_json(folder/'comparison.json',result);return result


def bindings(candidate,path,build=BUILD):
    """Bind native physical nets to the pinned legacy numeric HDL nodes."""
    require(candidate.compare(path)['passed'],'HR1 binding needs full native parity')
    native={(p.get('ref'),p.get('pin')):net.get('code') for net in ET.parse(path).getroot().findall('./nets/net') for p in net.findall('node')}
    refs={(c['board'],c['source_reference']):r for r,c in candidate.components.items()}
    rows=[]
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text())
    for board,targets in TARGETS.items():
        key=f'cp1-hct273/candidate/Circuits/KiCad/Compact/candidates/{board}.sch'
        source=build/key
        require(digest(source)==lock['artifacts'][key],'Changed HR1 legacy source')
        nets=connectivity(read_sheet(source));nodes={tuple(p):i for i,net in enumerate(nets) for p in net['nodes']}
        for ref in targets:
            nr=refs[board,ref];pins=[]
            for p in range(1,21):
                ni=nodes[ref,str(p)];peers=[]
                for r,pp in nets[ni]['nodes']:
                    if (board,r) in refs:
                        np=refs[board,r],pp
                        require(native[np]==native[nr,str(p)],'HR1 native/HDL net split')
                        peers.append(list(np))
                pins.append(dict(pin=str(p),hdl_node=ni,native_net=native[nr,str(p)],native_peers=sorted(peers)))
            def n(p):return f'n[{nodes[ref,str(p)]}]'
            def v(ps):return '{'+','.join(n(p) for p in reversed(ps))+'}'
            rows.append(dict(board=board,reference=nr,source_reference=ref,pins=pins,
                arguments=f'({v(DPINS)},{n(11)},{n(1)},{v(QPINS)},reset_n)',source_sha256=digest(source)))
    return rows


def loads(candidate,path):
    class Inventory(hb.md.LoadInventory):
        def classify(self,p):
            if p['part'] in (PART,hb.PART):
                self.parts[p['part']]=dict(input_pf=10,input_status='SCHS184C HCT CIN maximum10pF' if p['part']==PART else 'SCLS175I CIN maximum10pF',
                    input_full_OC1=True,inactive_output_pf=10,inactive_output_status='allocation-no-output-maximum',inactive_output_full_OC1=False,
                    selected_fixtures=[dict(arc='clock-Q' if p['part']==PART else 'data/enable/disable',load_pf=50)])
            super().classify(p)
    inv=Inventory(candidate,path);result=inv.audit(candidate);result['revision']='CP1-HR1'
    affected={p['net'] for p in inv.pins.values() if p['reference'] in candidate.targets and (p['receiver'] or p['driver'])}
    result['affected_nets']=[n for n in result['nets'] if n['net'] in affected]
    result['parts']=inv.parts
    result['source_conditions']=hp.parts()['377']
    result['dc_screen']=dict(vih_min_v=2,vil_max_v=0.8,input_supply_v=[4.5,5.5],
        output_supply_v=4.5,output_current_ma=4,voh_min_v=3.84,vol_max_v=0.33,temperature_c=[-40,85],
        scope='SCHS184C HCT table points; per-peer thresholds/rail offsets and actual loaded slew require full-link qualification.')
    result['families']=dict(Counter(next((f for f in ('AHCT','AHC','ACT','HCT','HC') if f in c['value']),'memory') for r,c in candidate.components.items() if r.startswith('U')))
    return result


def model_text(original,board,arcs,profile,fault=None):
    require(profile in (0,1,2,3),'Unknown HR1 profile')
    for index,row in enumerate(arcs):
        if row['board']!=board:continue
        ref=row['source_reference'];pattern=rf'al1_377 #\([^\n]+?\) {ref} (\([^\n]+\));'
        matches=list(re.finditer(pattern,original));require(len(matches)==1,'Missing HR1 instance '+ref)
        arguments=row['arguments']
        if fault=='enable' and board=='RG1' and ref=='U3':
            pins={p['pin']:p['hdl_node'] for p in row['pins']}
            arguments=arguments.replace(f",n[{pins['1']}],",f",n[{pins['20']}],")
        require(matches[0][1]==arguments,'HR1 HDL/native binding differs '+ref)
        delay=0 if profile==0 else 48 if profile==1 or index%2==profile-2 else 0
        original=re.sub(pattern,lambda m:f'hr1_377 #({delay},15,3,5,25,{int(board=="RG1")}) {ref} {arguments};',original)
    return original


def model_test(folder,case):
    folder=Path(folder);require(not folder.exists(),'Preserve HR1 model test');folder.mkdir(parents=True)
    # Fault stimuli have one intended timing failure; no reset masks a violation.
    bodies={
        'valid':"#60;if(q!==8'bx)$fatal(1,\"startup must be unknown\");reset_n=0;#60;if(q!==8'bx)$fatal(1,\"reset cleared storage\");enable_n=0;#30;clk=1;#60;if(q!==8'ha5)$fatal(1,\"capture during reset\");clk=0;#30;enable_n=1;reset_n=1;d=0;#30;clk=1;#60;if(q!==8'ha5)$fatal(1,\"disabled capture\");clk=0;reset_n=0;#60;if(q!==8'ha5)$fatal(1,\"asynchronous reset\");enable_n=0;#30;clk=1;#60;if(q!==0)$fatal(1,\"synchronous initialise\");",
        'data-hold':"#60;enable_n=0;#30;clk=1;#2;d=0;",
        'enable-hold':"#60;enable_n=0;#30;clk=1;#4;enable_n=1;",
        'data-setup':"#60;enable_n=0;#30;d=0;#14;clk=1;",
        'enable-setup':"#60;enable_n=0;#14;clk=1;",
        'high-pulse':"#60;clk=1;#24;clk=0;",
        'low-pulse':"#60;clk=1;#30;clk=0;#24;clk=1;",
        # Disable first, then change data. Relax TEH only in this monitor unit
        # stress case to isolate the old current-enable data-hold blind spot.
        'disabled-data-hold':"#60;enable_n=0;#30;clk=1;#1;enable_n=1;#1;d=0;",
        'missing-init':"#60;reset_n=0;#60;reset_n=1;",
        'reset-recovery':"#60;reset_n=0;enable_n=0;#2;clk=1;#60;if(q!==8'bx)$fatal(1,\"startup violation must poison\");clk=0;#60;clk=1;#60;if(q!==8'ha5)$fatal(1,\"clean init must recover\");clk=0;#60;reset_n=1;",
        'reset-no-recovery':"#60;reset_n=0;enable_n=0;#2;clk=1;#60;reset_n=1;"
    }
    params='48,15,3,0,25,1' if case=='disabled-data-hold' else '48,15,3,5,25,1'
    text='`timescale 1ns/1ps\nmodule tb;reg [7:0] d=8\'ha5;reg clk=0,enable_n=1,reset_n=1;wire [7:0] q;\n'
    text+=f'hr1_377 #({params}) dut(d,clk,enable_n,q,reset_n);initial begin '+bodies[case]+'#60;$display("PASS HR1 model");$finish;end endmodule\n'
    (folder/'tb.sv').write_text(text);(folder/'hct377.sv').write_text(MODEL.read_text())
    return execute(folder,['iverilog','-g2012','-s','tb','-o','test.vvp','hct377.sv','tb.sv'],'PASS HR1 model',60,dict(case=case))


def execute(folder,args,marker,timeout,meta):
    code,log=command(args,cwd=folder);(folder/'compile.log').write_text(log);require(code==0,'HR1 compile: '+log)
    code,log=command(['vvp','test.vvp'],cwd=folder,timeout=timeout);(folder/'simulation.log').write_text(log)
    rows=[]
    for line in log.splitlines():
        if line.startswith('HR1_SUMMARY '):
            fields=line.split();rows.append(dict(instance=fields[1],**{k:float(v) for k,v in (f.split('=') for f in fields[2:])}))
    result=dict(**meta,passed=code==0 and marker in log,exit_code=code,marker=marker,timing=rows,
        model_hashes={p.name:digest(p) for p in folder.glob('*.sv')},physical_qualification=False)
    write_json(folder/'result.json',result);print(folder.name,result['passed'],log[-250:],flush=True);return result


def simulate(folder,kind,case,profile,arcs,buffer_arcs):
    folder=Path(folder);require(not folder.exists(),'Preserve HR1 simulation');folder.mkdir(parents=True)
    lock=json.loads((VROOT/'targets/cp1/lock.json').read_text());prefix=COMPACT+case+'/'
    params={};boards={}
    if kind=='registers':
        top='register_hardware_tb';names=['registers.sv','clock.sv','fabric.sv','support.sv','tb.sv'];boards={'registers.sv':'RG1'};marker='DONE RG1'
    elif kind=='alu':
        top='alu_hardware_tb';names=['module.sv','clock.sv','support.sv','tb.sv','alu.bin','vectors.hex'];boards={'module.sv':'AL1'};params={'QUICK':0 if 'quick0' in case else 1};marker='DONE AL1'
    else:
        top='sequencer_tb';names=[b+'.sv' for b in hb.io_cpu.BOARDS]+['support.sv','tb.sv','alu.bin','control.hex'];boards={'AL1.sv':'AL1','RG1.sv':'RG1'}
        params={p:1 for p in ('HARD_ALU','HARD_REGISTERS','HARD_ADDRESS','HARD_MEMORY')}
        if kind=='boot':
            prefix='cp1-text-boot/'+case+'/';lock=json.loads(hb.text_boot_evidence.LOCK.read_text())
            names+=['bridge.sv','text.sv','boot-rom.hex','sram-power-on.hex','payload.hex','serial-expected.hex'];marker='PASS TB1 ROM reconstruction'
        else:
            names+=['cases.txt','instructions.txt','expected.txt','program.hex'];params['CASE_SUITE']=1;marker='DONE fetched-opcodes'
    inputs=hb.ms.collect(folder,prefix,lock,names)
    for name,board in boards.items():(folder/name).write_text(model_text((folder/name).read_text(),board,arcs,profile,'enable' if case=='registers-c1-enable' else None))
    if kind in ('boot','instructions'):
        # Actual HB1 maximum buffer delay is retained even in fast HCT377 profiles.
        p=folder/'ME1.sv';p.write_text(hb.memory_model(p.read_text(),buffer_arcs,1))
    (folder/'hct377.sv').write_text(MODEL.read_text())
    sources=[n for n in names if n.endswith('.sv')]+['hct377.sv']
    if kind=='boot':sources+=[VROOT/'hdl/text_cells.sv']
    args=['iverilog','-g2012','-s',top,'-o','test.vvp']
    for k,v in params.items():args+=['-P',f'{top}.{k}={v}']
    args+=sources
    result=execute(folder,args,marker,1800,dict(kind=kind,case=case,profile=profile,input_hashes=inputs,buffer_profile=1 if kind in ('boot','instructions') else None))
    return result


JOBS=[('registers-'+str(p),'registers',f'registers-c{c}-valid',p) for p,c in [(0,0),(1,1),(2,5)]]+[
    ('registers-'+f,'registers','registers-c1-'+f,1) for f in ('enable','init-clock')]+[
    ('alu-max','alu','alu-module-c1-quick0',1),('alu-mixed','alu','alu-module-c4-quick1',2)]+[
    ('instructions-'+str(p),'instructions',f'c{c}-cases1',p) for p,c in [(0,0),(1,1),(2,7)]]+[
    ('boot-'+case,'boot',case,p) for case,p in [('guarded-max',1),('zero',0),('mixed2',2),('mixed3',3)]]
MODEL_CASES=('valid','data-hold','enable-hold','data-setup','enable-setup','high-pulse','low-pulse','disabled-data-hold','missing-init','reset-recovery','reset-no-recovery')


def run(folder):
    he.load();folder=Path(folder);require(not folder.exists(),'Preserve HR1 study');folder.mkdir(parents=True)
    c=Candidate();native=c.generate(folder/'native');require(native['passed'],'HR1 native parity')
    faults={f:c.generate(folder/f,f) for f in NATIVE_FAULTS};require(all(not r['passed'] for r in faults.values()),'HR1 native mutation missed')
    arcs=bindings(c,folder/'native/HR1.xml');write_json(folder/'bindings.json',arcs)
    buffer_arcs=c.bindings(folder/'native/HR1.xml');write_json(folder/'buffer-bindings.json',buffer_arcs)
    write_json(folder/'loads.json',loads(c,folder/'native/HR1.xml'))
    model={case:model_test(folder/('model-'+case),case) for case in MODEL_CASES}
    def once(job):
        name,kind,case,p=job;return name,simulate(folder/name,kind,case,p,arcs,buffer_arcs)
    with ThreadPoolExecutor(max_workers=3) as pool:results=dict(pool.map(once,JOBS))
    summary=dict(revision='CP1-HR1',native=native,native_faults=faults,model_tests=model,results=results,
        physical_qualification=False,promoted_into_R2=False)
    write_json(folder/'summary.json',summary)
    require(all(r['passed']==(case in ('valid','reset-recovery')) for case,r in model.items()),'HR1 model outcomes')
    require(all(r['passed']==(name not in ('registers-enable','registers-init-clock')) for name,r in results.items()),'HR1 diagnostic outcomes')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.output)
