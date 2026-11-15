"""CP1 component/net-derived models, using existing CPU interface bindings."""
from collections import defaultdict
import json
from .common import ROOT,VROOT,BUILD
from .legacy import read_sheet,connectivity,function_number
from .controller_hardware import Circuit as Word
from .alu_hardware import Circuit as Alu
from .address_hardware import Circuit as Address
from .memory_hardware import Circuit as Memory
from .pc_hardware import Circuit as Pc
from .sequencer import Circuit as Sequencer
from .clock import Clock

def parts():
    devices={}
    for group in ('clock','controller','alu','pc','address','memory'):
        for name,d in json.loads((VROOT/f'{group}-parts.json').read_text())['devices'].items():
            devices.setdefault(name,{}).update(d)
    aliases={'CD74AC175M96':'CD74ACT175E','CD74HCT161M96':'CD74HCT161E',
             'CD74HCT154M96':'CD74HCT154E','SN74AHCT00DR':'SN74AHCT00N','SN74AHCT08DR':'SN74AHCT08N'}
    for old,new in aliases.items():devices[new]=dict(devices[old],package='DIP')
    devices['CD74ACT175E'].update(max_delay_ns=13,source='cd74act175',pulse_ns=5,clear_pulse_ns=4)
    devices['SN74HC377N']=dict(function='377',source='sn74hc377',package='DIP-20',max_delay_ns=40,
        setup_ns=25,hold_ns=5,enable_hold_ns=5,pulse_ns=25,input_cap_pf=10,vih_min_v=3.15,vil_max_v=1.35)
    devices['SN74HCT273N']=dict(function='273',source='sn74hct273',package='DIP-20',max_delay_ns=42,
        setup_ns=25,hold_ns=0,recovery_ns=25,pulse_ns=25,clear_pulse_ns=20,input_cap_pf=10)
    devices['CD74HCT191E']=dict(function='191',source='cd74hct191',package='DIP-16',max_delay_ns=50,
        clock_q_ns=34,clock_rco_ns=44,clock_tc_ns=53,data_q_ns=48,load_q_ns=50,
        data_setup_ns=15,data_hold_ns=2,enable_setup_ns=15,enable_hold_ns=2,direction_setup_ns=23,
        recovery_ns=15,load_pulse_ns=20,pulse_ns=25,input_cap_pf=10)
    devices['SN74HCT245N']=dict(function='245',source='sn74hct245',package='DIP-20',max_delay_ns=38,
        enable_max_ns=74,disable_max_ns=50,input_cap_pf=10,io_cap_pf=None,timing_load_pf=150,
        limitation='150 pF data/enable bounds; disable table is 50 pF only. No guaranteed IO-port capacitance provided.')
    devices['M27C1024-10F1']=dict(function='M27C1024',source='m27c1024',package='DIP-40',max_delay_ns=100,
        input_cap_pf=6,timing_load_pf=100)
    devices['W27C512-45Z']=dict(function='27C512',source='w27c512',package='DIP-28',max_delay_ns=45,
        input_cap_pf=6,output_hold_ns=0)
    devices['UM61512AK-15']=dict(function='UM61512',source='um61512a',package='DIP-32',max_delay_ns=15,
        disable_max_ns=10,input_cap_pf=8,io_cap_pf=10,timing_load_pf=30,write_cycle_ns=15,
        address_write_setup_ns=12,write_pulse_ns=9,write_data_setup_ns=7,write_data_hold_ns=0)
    return dict(devices=devices,constraints=dict(local_trace_cap_pf=5,connector_load_pf=10,data_bus_external_load_pf=0))

class Circuit(Word):
    def __init__(self,name,sheet=None):
        self.name=name;self.sheet=sheet or read_sheet(ROOT/f'Circuits/KiCad/Compact/candidates/{name}.sch')
        self.parts=parts();self.nets=connectivity(self.sheet)
        self.nodes={tuple(node):i for i,net in enumerate(self.nets) for node in net['nodes']}
        self.labels={label:i for i,net in enumerate(self.nets) for label in net['labels']}
        self.components=defaultdict(list)
        for c in self.sheet['components']:
            if not c['ref'].startswith('U'):continue
            d=self.parts['devices'][c['value']];s=c['lib_id'].split(':')[1]
            if (function_number(s) or s)!=d['function']:raise ValueError((name,c['ref'],s,d['function']))
            self.components[c['ref']].append(c)
        self.parts['devices']={cs[0]['value']:self.parts['devices'][cs[0]['value']] for cs in self.components.values()}
    loads=Alu.loads
    rom_address_hdl=Alu.rom_address_hdl

    def extra_hdl(self,ref,kind,d,delay):
        n=self.n;v=self.vector
        if kind=='273':return [f'cp273 #({delay(d["max_delay_ns"])}) {ref} '
            f'({v(ref,[3,4,7,8,13,14,17,18])},{n(ref,11)},{n(ref,1)},{v(ref,[2,5,6,9,12,15,16,19])});']
        if kind=='377':return [f'al1_377 #({delay(d["max_delay_ns"])},25,5,5,25) {ref} '
            f'({v(ref,[3,4,7,8,13,14,17,18])},{n(ref,11)},{n(ref,1)},{v(ref,[2,5,6,9,12,15,16,19])},reset_n);']
        if kind=='574':return [f'cw574 #({delay(d["max_delay_ns"])},25,5,20) {ref} '
            f'({v(ref,range(2,10))},{n(ref,11)},{n(ref,1)},{v(ref,range(19,11,-1))},reset_n);']
        if kind=='191':return [f'cp191 #({delay(34)},{delay(44)},{delay(53)},{delay(50)},{delay(48)}) {ref} '
            f'({v(ref,[15,1,10,9])},{n(ref,14)},{n(ref,11)},{n(ref,4)},{n(ref,5)},'
            f'{v(ref,[3,2,6,7])},{n(ref,12)},{n(ref,13)},reset_n);']
        if kind=='74':
            rows=[]
            for c in self.components[ref]:
                if c['unit']==3:continue
                di,cl,cr,pr,q,nq=(2,3,1,4,5,6) if c['unit']==1 else (12,11,13,10,9,8)
                if self.nodes[ref,str(pr)]!=self.labels['5V']:raise ValueError('Preset must be inactive')
                rows.append(f'clock_ff #({delay(11)},{delay(11)},5,0.5,3) {ref}_{c["unit"]}'
                    f'({n(ref,di)},{n(ref,cl)},{n(ref,cr)},{n(ref,q)},{n(ref,nq)},reset_n);')
            return rows
        if kind=='245':
            if self.nodes[ref,'1']!=self.labels['5V']:raise ValueError('CP1 transceiver direction is fixed A to B')
            # A separate delayed drive-state wire exposes same-data contention.
            # Pin-level outputs and monitor use the identical delay selection.
            ton=delay(max(d['max_delay_ns'],d['enable_max_ns']));toff=delay(d['disable_max_ns'])
            return [f'wire cp_active_{ref};assign #({ton},{toff}) cp_active_{ref}=~{n(ref,19)};']+[
                f'bufif0 #({ton},{ton},{toff}) {ref}_{i} ({n(ref,18-i)},{n(ref,2+i)},{n(ref,19)});' for i in range(8)]
        if kind=='UM61512':return [f'cp_sram #({delay(15)},{delay(10)},15,12,9,7) {ref} '
            f'({v(ref,[12,11,10,9,8,7,6,5,27,26,23,25,4,28,3,31])},{n(ref,22)},{n(ref,30)},{n(ref,24)},{n(ref,29)},'
            f'{v(ref,[13,14,15,17,18,19,20,21])},reset_n);']
        if kind=='27C512':return Memory.extra_hdl(self,ref,kind,d,delay)
        if kind=='M27C1024':return [f'cp_control_rom #({delay(100)}) {ref} '
            f'({v(ref,list(range(21,30))+list(range(31,38)))},{n(ref,2)},{n(ref,20)},'
            f'{v(ref,list(range(19,11,-1))+list(range(10,2,-1)))});']
        if kind=='154':
            pins=[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,17]
            return [f'assign #({delay(d["max_delay_ns"])}) {n(ref,p)}=({n(ref,18)} || {n(ref,19)}) ? 1\'b1 : '
                    f'({v(ref,[23,22,21,20])} != 4\'d{b});' for b,p in enumerate(pins)]
        raise ValueError('Unmodelled compact device '+kind)

    logic_hdl=Address.logic_hdl
    def hdl(self,corner=0):
        from designs.compact_candidate import SOURCE_GROUPS
        text=self._hdl(corner)
        if self.name in SOURCE_GROUPS:
            text=text.replace(');',',inout [7:0] source_bus);',1)
            text=text.replace('\nendmodule','\n'+'\n'.join(f'tran ({self.n("J91",b+3)},source_bus[{b}]);' for b in range(8))+'\nendmodule',1)
        return text

    def _hdl(self,corner=0):
        n=self.n
        if self.name=='PC1':return Pc.hdl(self,corner)
        if self.name=='SQ1':return Sequencer.hdl(self,corner)
        if self.name=='AL1':return Alu.hdl(self,corner)
        if self.name=='ME1':return Memory.hdl(self,corner)
        if self.name=='C1':
            c=Clock.__new__(Clock);c.__dict__.update(self.__dict__)
            c.parts.update({k:v for k,v in json.loads((VROOT/'clock-parts.json').read_text()).items() if k!='devices'})
            # Merge constraints, preserve physical pin-derived clock load audit.
            text=Clock.hdl(c,corner)
            old=f'assign {n("Y1",8)}=osc;';new=f'assign {n("Y1",5)}=osc;'
            assert text.count(old)==1;text=text.replace(old,new)
            text=text.replace('output [3:0] state);','output [3:0] state,output init_clk,system_reset_n);')
            return text.replace('\nendmodule',f'\nassign init_clk={n("J90",3)};assign system_reset_n={n("J90",4)};\nendmodule',1)
        if self.name in ('SP1','MA1'):
            self.kind='mar' if self.name=='MA1' else 'stack'
            text=Address.hdl(self,corner)
            text=text.replace('output [15:0] address);','output [15:0] address,input init_clk,ph2);') if self.kind=='mar' else text.replace('output [15:0] address,sp);','output [15:0] address,sp,input init_clk,ph2);')
            return text.replace('\nendmodule',f'\nassign {n("J90",3)}=init_clk;assign {n("J90",4)}=ph2;\nendmodule')
        if self.name=='BF1':
            lines=['module compact_bus(inout [31:0] branches,input [13:0] enable_n,inout [7:0] data_bus,input reset_n);']
            lines += [f'assign {n("J7",3)}=reset_n;']
            for group in range(4):
                lines += [f'tran ({n("J"+str(group+1),b+3)},branches[{8*group+b}]);' for b in range(8)]
            lines += [f'tran ({n("J5",b+3)},data_bus[{b}]);' for b in range(8)]
            lines += [f'assign {n("J6",b+3)}=enable_n[{b}];' for b in range(14)]
        elif self.name=='DT1':
            from designs.compact_candidate import LEAVES
            lines=[f'module compact_distribution(input [3:0] phase,input init_clk,reset_n,output [{len(LEAVES)-1}:0] leaves);']
            lines += [f'assign {n("J1",b+3)}=phase[{b}];' for b in range(4)]
            lines += [f'assign {n("J1",7)}=init_clk;assign {n("J1",8)}=reset_n;']
            lines += [f'assign leaves[{i}]={n("J2",i+3)};' for i in range(len(LEAVES))]
        elif self.name=='RG1':
            lines=['module general_registers(input ph3,reset_n,input [3:0] load_n,out_n,inout [7:0] data_bus,output [31:0] registers,input init_clk);',
                f'assign {n("J1",3)}=ph3;assign {n("J1",4)}=reset_n;assign {n("J90",3)}=init_clk;']
            for i,r in enumerate('BCHL'):
                lines += [f'assign {n("J1",5+i)}=load_n[{i}];assign {n("J1",9+i)}=out_n[{i}];']
                lines += [f'assign registers[{24-8*i+b}]=n[{self.labels[f"{r}{b}"]}];' for b in range(8)]
            lines += [f'tran ({n("J2",b+3)},data_bus[{b}]);' for b in range(8)]
        elif self.name=='CW1':
            lines=['module control_word(input ph1,ph2,reset_n,input [15:0] address,output [15:0] word,output [14:1] out_n,load_n,output [12:1] functions,output [4:0] alu_op,output alu_enable,pc_address_n,valid);']
            for p,s in [(3,'ph1'),(4,'ph2'),(5,'reset_n')]:lines += [f'assign {n("J1",p)}={s};']
            for b in range(16):lines += [f'assign {n("J2",b+3)}=address[{b}];']
            for b in range(1,15):lines += [f'assign out_n[{b}]={n("J3",b+2)};assign load_n[{b}]={n("J4",b+2)};']
            for b in range(1,13):lines += [f'assign functions[{b}]={n("J5",b+2)};']
            for b in range(5):lines += [f'assign alu_op[{b}]={n("J6",b+3)};']
            lines += [f'assign pc_address_n={n("J6",8)};assign alu_enable={n("J6",9)};assign valid={n("J1",6)};']
            lines += ['assign word={'+','.join(n(f'U{3+b//8}',19-b%8) for b in reversed(range(16)))+'};']
        else:raise ValueError(self.name)
        lines.insert(1,f'tri n [0:{len(self.nets)-1}];')
        lines += [f'assign n[{self.labels["5V"]}]=1;assign n[{self.labels["GND"]}]=0;']
        return '\n'.join(['`timescale 1ns/1ps']+lines+self.logic_hdl(corner)+['endmodule'])

def support_hdl():
    # Keep the SRAM bus algorithm, but use the actual 16-address-pin/64K array.
    mem=(VROOT/'hdl/memory_devices.sv').read_text().split('module me_sram',1)[1]
    mem=('module cp_sram'+mem).replace('[16:0]','[15:0]').replace('[0:131071]','[0:65535]')
    return (VROOT/'hdl/compact_devices.sv').read_text()+'\n'+mem
