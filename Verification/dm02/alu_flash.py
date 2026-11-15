"""AL2 staged ALU with private-output flash, startup contract and fetched proof."""
import shutil
from .common import ROOT,VROOT,BUILD,digest,evidence,write_json
from .legacy import read_sheet
from .alu_hardware import Circuit as Alu,simulate,fixtures,budget as alu_budget
from .flash_hardware import MPN,flash_hdl,images,image_name,sources
from .electrical import audit
from .native_migrate import validate

SOURCE=ROOT/'Circuits/KiCad/ALU/candidates/Flash-ALU.sch'


class Circuit(Alu):
    def __init__(self,sheet=None):super().__init__(sheet or read_sheet(SOURCE),parts_file='alu-flash-parts.json')

    @property
    def power_on_wait_ns(self):return self.parts['devices'][MPN]['startup_ns']+1000

    def rom_address_hdl(self):
        names=[f'B{i}' for i in range(8)]+[f'A{i}' for i in range(8)]+[f'OP{i}' for i in range(5)]
        return 'assign rom_address={'+','.join(f'n[{self.labels[name]}]' for name in reversed(names))+'};'

    def extra_hdl(self,ref,kind,d,delay):
        if kind=='SST39SF040':return flash_hdl(self,ref,d,delay,101)
        return super().extra_hdl(ref,kind,d,delay)

    def hdl(self,corner=0):
        guard=f'always @(posedge reset_n) if($realtime>0 && $realtime<{self.parts["devices"][MPN]["startup_ns"]}) $fatal(1,"AL2 flash startup reset contract");'
        return super().hdl(corner).replace('\nendmodule','\n'+guard+'\nendmodule',1)+'\n'+(VROOT/'hdl/flash_devices.sv').read_text()

    def prepare_simulation(self,folder):
        # Existing fetched/operand fixtures store ALU words big-endian for $fread.
        big=(folder/'alu.bin').read_bytes()
        raw=bytearray(len(big));raw[0::2]=big[1::2];raw[1::2]=big[0::2]
        images(folder,raw)


def budget(c,timing=None):
    legacy=Alu()
    for name,device in legacy.parts['devices'].items():
        if name!='M27C322-100F1' and c.parts['devices'][name]!=device:raise ValueError('AL2 staged-device limits diverged; rederive timing paths')
    paths=alu_budget(legacy,timing);d=c.parts['devices']
    flash_path=d['SN74AHCT244N']['max_delay_ns']+d[MPN]['max_delay_ns']+2*d['SN74AHCT157N']['max_delay_ns']
    paths[0]['path']='PH3 operands through buffered flash/bank mux to PH1 result snapshot'
    paths[0]['required_ns']+=flash_path-legacy.parts['devices']['M27C322-100F1']['max_delay_ns']
    paths[0]['margin_ns']=paths[0]['available_ns']-paths[0]['required_ns']
    return paths


def run():
    from .register_hardware import Circuit as Registers,bus_load
    from .address_hardware import AddressPath
    from .memory_hardware import Circuit as Memory
    from .pc_hardware import Circuit as Pc
    from .sequencer import Circuit as Seq
    from .instruction_fixtures import generate
    from .hardware_programs import fixtures as demo_fixtures,render
    folder=BUILD/'alu-flash';folder.mkdir(parents=True,exist_ok=True);c=Circuit();address=AddressPath()
    native=validate(c.sheet,folder/'native');structure=audit(c.sheet);loads=c.loads();paths=budget(c);retained=sources(folder,c.parts)
    coverage=fixtures(folder/'fixtures');opcodes=generate(folder/'fixtures');programming=images(folder/'images')
    bus=bus_load([('AL2',c),('PC1',Pc()),('SQ1',Seq()),('RG1',Registers()),('SP1',address.stack),('MA1',address.mar),('ME1',Memory())])
    runs=[];demos=[]
    for connected,cases in [(False,False),(True,False),(True,True)]:
        for corner in (0,1,2):
            name=f'corner{corner}-connected{int(connected)}-cases{int(cases)}'
            partners=dict(registers=Registers(),address_path=address,memory=Memory()) if connected else {}
            r=simulate(c,folder/name,corner,folder/'fixtures',connected,cases=cases,**partners);r.pop('log')
            r['log_path']=f'alu-flash/{name}/alu.log';runs.append(r)
    for name in ('hello_world','emulator_demo'):
        dest=folder/name;trace=demo_fixtures(dest/'fixtures',name)
        r=simulate(c,dest/'maximum',1,dest/'fixtures',True,registers=Registers(),address_path=address,memory=Memory(),demo=True);r.pop('log')
        output=render(dest/'maximum',name) if r['passed'] else None
        demos.append(dict(name=name,coverage=trace,simulation=r,output=output,
                          passed=bool(r['passed'] and output['passed'] and output['io_events']==trace['io_events'])))
    passed=(native['status']=='pass' and not structure['findings'] and all(r['passed'] for r in runs+demos)
            and all(r['characterized'] for r in loads if not r['shared_data_bus']) and all(r['margin_ns']>=0 for r in paths))
    scope=('AL2 replaces the obsolete ALU ROM with eight SST39SF040 PLCC32 flash devices while retaining staged A/operand/result/flag storage. '
           'Nine operand/continuous/all-opcode profiles and both maximum-delay demos use the normal repository harness. '
           'The fixture delays reset release through flash startup; there is no physical supervisor or loader. '
           'Shared DATA remains 90–100 pF before routing/output capacitance. SRAM turnaround, clock/reset, flash programming/readback '
           'and physical electrical qualification remain open; AL1 is retained separately.')
    shutil.copyfile(SOURCE,folder/SOURCE.name);write_json(folder/'parts.json',c.parts);write_json(folder/'bus-load.json',bus)
    write_json(folder/'summary.json',dict(source_hash=digest(SOURCE),parts=c.parts,sources=retained,native=native,structure=structure,
                loads=loads,timing_paths=paths,coverage=coverage,opcode_coverage=opcodes,images=programming,runs=runs,demos=demos,bus_load=bus,scope=scope))
    artifacts=['alu-flash/'+s for s in ('summary.json','parts.json','bus-load.json','Flash-ALU.sch','native/Flash-ALU.kicad_sch','images/images.json')]
    artifacts.extend(r['log_path'] for r in runs)
    for d in demos:
        artifacts.extend(f'alu-flash/{d["name"]}/'+p for p in ('fixtures/coverage.json','maximum/alu.log'))
        if d['output']:artifacts.extend(f'alu-flash/{d["name"]}/maximum/'+p for p in ('io-observed.txt','display.pgm','text.txt'))
    artifacts.extend(f'alu-flash/images/{image_name(bank,lane)}' for bank in range(4) for lane in range(2))
    artifacts.extend(str(p.relative_to(BUILD)) for p in (folder/'sources').rglob('*.txt'))
    return evidence('alu-flash','Flash ALU and complete-machine demos','limited' if passed else 'fail',
                    f'{sum(r["passed"] for r in runs)}/9 profiles; {sum(d["passed"] for d in demos)}/2 demos; '
                    '227 fetched opcodes and 2,282,809 demo cycles; eight flash images replace the legacy ALU ROM.',artifacts=artifacts,limitation=scope)
