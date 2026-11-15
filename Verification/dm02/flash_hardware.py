"""FR1 read-only flash array and exact bank/lane programming images."""
import hashlib
import json
import shutil
from .common import ROOT,VROOT,BUILD,command,digest,evidence,write_json
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu
from .address_hardware import Circuit as Logic
from .electrical import audit
from .native_migrate import validate

SOURCE=ROOT/'Circuits/KiCad/ALU/candidates/Flash-Array.sch'
MPN='SST39SF040-70-4I-NHE'
APINS=[12,11,10,9,8,7,6,5,27,26,23,25,4,28,29,3,2,30,1]
DPINS=[13,14,15,17,18,19,20,21]


def image_name(bank,lane):return f'bank{bank}-'+('high' if lane else 'low')+'.bin'


def images(folder,raw=None):
    """Input is the complete little-endian 2M-word ALU image."""
    folder.mkdir(parents=True,exist_ok=True)
    if raw is None:raw=b''.join((BUILD/'alu'/f'alu{i}.rom').read_bytes() for i in range(8))
    if len(raw)!=4194304:raise ValueError('FR1 requires exactly 2,097,152 16-bit words')
    records=[];recovered=bytearray(len(raw))
    for bank in range(4):
        for lane in range(2):
            name=image_name(bank,lane);data=raw[bank*1048576+lane:(bank+1)*1048576:2]
            (folder/name).write_bytes(data)
            records.append(dict(bank=bank,lane=lane,file=name,bytes=len(data),sha256=digest(folder/name)))
    # Read all persisted bytes back, independently expressing word-address mapping.
    loaded={(r['bank'],r['lane']):(folder/r['file']).read_bytes() for r in records}
    for address in range(2097152):
        bank=address>>19;local=address&0x7ffff
        recovered[2*address]=loaded[bank,0][local];recovered[2*address+1]=loaded[bank,1][local]
    if recovered!=raw:raise ValueError('FR1 bank/lane reconstruction mismatch')
    (folder/'alu-original.bin').write_bytes(raw)
    result=dict(words_verified=2097152,original_sha256=hashlib.sha256(raw).hexdigest(),images=records,
                mapping='bank=address[20:19], local=address[18:0]; lane 0=low byte, lane 1=high byte',
                scope='Logical programming-image reconstruction only; no physical programming/readback evidence.')
    write_json(folder/'images.json',result);return result


def flash_hdl(c,ref,d,delay,first_ref=1):
    index=int(ref[1:])-first_ref
    if not 0<=index<8:raise ValueError('FR1 flash reference does not map to a bank/lane')
    return [f'flash_read #({delay(d["max_delay_ns"])},{d["startup_ns"]},"{image_name(index//2,index%2)}") {ref} '
            f'({c.vector(ref,APINS)},{c.n(ref,22)},{c.n(ref,24)},{c.n(ref,31)},{c.vector(ref,DPINS)});']


class Circuit(Logic):
    def __init__(self,sheet=None):Alu.__init__(self,sheet or read_sheet(SOURCE),parts_file='flash-parts.json')

    def extra_hdl(self,ref,kind,d,delay):
        if kind=="SST39SF040":return flash_hdl(self,ref,d,delay)
        return super().extra_hdl(ref,kind,d,delay)

    def hdl(self,corner=0):
        n=self.n
        lines=['`timescale 1ns/1ps','module flash_array(input [20:0] address,output [15:0] result);',
               f'tri n[0:{len(self.nets)-1}];',f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        for b in range(21):lines.append(f'assign {n("J1",b+3)}=address[{b}];')
        for b in range(16):lines.append(f'assign result[{b}]={n("J2",b+3)};')
        return '\n'.join(lines+self.logic_hdl(corner)+['endmodule',(VROOT/'hdl/flash_devices.sv').read_text()])


def simulate(c,folder,fixture,corner=0):
    folder.mkdir(parents=True,exist_ok=True)
    for name in ['alu-original.bin']+[image_name(bank,lane) for bank in range(4) for lane in range(2)]:
        shutil.copyfile(fixture/name,folder/name)
    (folder/'flash.sv').write_text(c.hdl(corner))
    code,log=command(['iverilog','-g2012','-s','flash_array_tb','-o','flash.vvp','flash.sv',VROOT/'hdl/flash_array_tb.sv'],cwd=folder)
    if code:raise RuntimeError('FR1 compile: '+log)
    code,out=command(['vvp','flash.vvp'],cwd=folder,timeout=180);log+=out;(folder/'flash.log').write_text(log)
    return dict(passed=code==0 and 'DONE FR1 checks=32776' in log,corner=corner,log=log)


def sources(folder,parts):
    needed={d['source'] for d in parts['devices'].values()};retained=[]
    for group in ('flash','alu','controller','pc','clock'):
        manifest=json.loads((VROOT/f'vendor/{group}/manifest.json').read_text())
        for entry in manifest['files']:
            if entry['id'] not in needed:continue
            source=VROOT/f'vendor/{group}'/entry['file']
            if digest(source)!=entry['sha256']:raise ValueError('Flash candidate source excerpt changed')
            dest=folder/'sources'/group/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
            retained.append(dict(group=group,**entry))
    if {r['id'] for r in retained}!=needed:raise ValueError('Flash candidate manufacturer provenance missing')
    for entry in json.loads((VROOT/'vendor/flash/manifest.json').read_text()).get('programmer',[]):
        source=VROOT/'vendor/flash'/entry['file']
        if digest(source)!=entry['sha256']:raise ValueError('Flash programmer support excerpt changed')
        dest=folder/'sources/flash'/entry['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
        retained.append(dict(group='flash',**entry))
    return retained


def run():
    c=Circuit();folder=BUILD/'flash-array';folder.mkdir(parents=True,exist_ok=True)
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads()
    coverage=images(folder/'images');retained=sources(folder,c.parts);runs=[]
    for corner in (0,1,2):
        r=simulate(c,folder/f'corner{corner}',folder/'images',corner);r.pop('log');runs.append(r)
    scope=('FR1 uses eight SST39SF040-70-4I-NHE PLCC devices, private outputs and two-stage bank selection. '
           'All 2,097,152 words reconstruct from eight 524,288-byte images; each delay profile reads 32,776 addresses '
           'and checks the 100 us startup boundary. ALU integration is a separate candidate. '
           'Full-temperature capacitance, physical programming/readback, supply startup and PCB qualification remain open.')
    passed=native['status']=='pass' and not structure['findings'] and all(r['characterized'] for r in loads) and all(r['passed'] for r in runs)
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts)
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),native=native,structure=structure,loads=loads,images=coverage,
                                        parts=c.parts,sources=retained,runs=runs,scope=scope))
    artifacts=[str(p.relative_to(BUILD)) for p in folder.rglob('*') if p.is_file() and p.suffix in ('.json','.log','.bin','.txt','.sch','.kicad_sch')]
    return evidence('flash-array','Private-output ALU flash replacement array','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/3 profiles; 32,776 pin-derived reads per profile; 2,097,152 words reconstructed from eight programming images.',
                    artifacts=sorted(artifacts),limitation=scope)
